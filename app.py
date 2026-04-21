"""
Flask API Server for Chinese TTS Video Generation
"""
import os
import uuid
import json
from datetime import datetime
from pathlib import Path
from threading import Thread
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from config import config
from tts_generator import create_video
from threading import Lock


# Configuration
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config.from_object(config)
CORS(app)

UPLOAD_FOLDER = config.UPLOAD_FOLDER
UPLOAD_FOLDER.mkdir(exist_ok=True)
MAX_VIDEO_FILES = config.MAX_VIDEO_FILES   # chỉ giữ tối đa 10 file

# In-memory job tracking (in production, use Redis or database)
jobs = {}
generation_lock = Lock()


def cleanup_excess_files():
    """
    Nếu số file mp4 > MAX_VIDEO_FILES
    thì xóa file cũ nhất cho tới khi còn đúng MAX_VIDEO_FILES
    """
    files = list(UPLOAD_FOLDER.glob("*.mp4"))

    if MAX_VIDEO_FILES < 0 or len(files) <= MAX_VIDEO_FILES:
        return

    # sort theo thời gian sửa đổi cũ -> mới
    files.sort(key=lambda f: f.stat().st_mtime)

    files_to_delete = files[:-MAX_VIDEO_FILES]

    for file in files_to_delete:
        try:
            file.unlink()
            print(f"🗑 Deleted old file: {file.name}")
        except Exception as e:
            print(f"❌ Cannot delete {file.name}: {e}")

def validate_content(content):
    """Validate content length"""
    if not content or len(content) > 1000:
        return False, "Content must be between 1 and 1000 characters"
    return True, "Valid"


def validate_parameters(data):
    """Validate all input parameters"""
    errors = []
    
    # Validate speech speed
    try:
        speed = float(data.get('speech_speed', 0.9))
        if speed < 0.1 or speed > 2.0:
            errors.append("Speech speed must be between 0.1 and 2.0")
    except (ValueError, TypeError):
        errors.append("Invalid speech speed value")
    
    # Validate delay
    try:
        delay = float(data.get('delay', 0.2))
        if delay < 0 or delay > 1:
            errors.append("Delay must be between 0 and 1")
    except (ValueError, TypeError):
        errors.append("Invalid delay value")
    
    # Validate content
    content = data.get('content', '').strip()
    is_valid, msg = validate_content(content)
    if not is_valid:
        errors.append(msg)
    
    return errors if errors else None, content


def generate_video_task(job_id, text, speech_speed, delay):
    """Background task to generate video"""
    try:
        output_path = UPLOAD_FOLDER / f"{job_id}.mp4"
        print(f"[Job {job_id[:8]}] Starting video generation...")
        create_video(text, speech_speed, delay, str(output_path))
        # cleanup sau khi tạo xong file mới
        cleanup_excess_files()
        
        jobs[job_id] = {
            'status': 'completed',
            'file_path': str(output_path),
            'completed_at': datetime.now().isoformat()
        }
        print(f"[Job {job_id[:8]}] ✅ Video generation completed")
    except Exception as e:
        error_msg = str(e)
        print(f"[Job {job_id[:8]}] ❌ Error: {error_msg}")
        jobs[job_id] = {
            'status': 'failed',
            'error': error_msg
        }
    finally:
        # VERY IMPORTANT: always unlock
        generation_lock.release()
        print("🔓 Server is ready for next request")

# ============ WEB ROUTES ============

@app.route('/')
def index():
    """Serve main web UI"""
    return render_template('index.html')


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)


# ============ API ROUTES ============

@app.route('/api/videos', methods=['GET'])
def list_videos():
    """
    Get all videos in uploads folder

    Response:
    {
        "count": 3,
        "videos": [
            {
                "id": "uuid",
                "filename": "uuid.mp4",
                "url": "/api/videos/uuid",
                "size": 123456,
                "created_at": "2026-04-21T23:10:00"
            }
        ]
    }
    """
    try:
        files = list(UPLOAD_FOLDER.glob("*.mp4"))

        videos = []

        for file in files:
            stat = file.stat()

            videos.append({
                "id": file.stem,                 # filename không có .mp4
                "filename": file.name,
                "url": f"/api/videos/{file.stem}",
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(
                    stat.st_mtime
                ).isoformat()
            })

        # mới nhất lên đầu
        videos.sort(
            key=lambda x: x["created_at"],
            reverse=True
        )

        return jsonify({
            "count": len(videos),
            "videos": videos
        }), 200

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500
        
@app.route('/api/generate', methods=['POST'])
def generate():
    """
    Generate video from text
    
    Request body:
    {
        "content": "Chinese text...",
        "speech_speed": 0.9,
        "delay": 0.2
    }
    
    Response:
    {
        "job_id": "uuid",
        "status": "pending",
        "message": "Video generation started"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        # Reject if busy
        if not generation_lock.acquire(blocking=True):
            return jsonify({
                'error': 'Server is busy generating another video. Please try again later.'
            }), 429

        # Validate parameters
        errors, content = validate_parameters(data)
        if errors:
            generation_lock.release()
            return jsonify({'error': ' '.join(errors)}), 400

        job_id = str(uuid.uuid4())
        speech_speed = float(data.get('speech_speed', 0.9))
        delay = float(data.get('delay', 0.2))

        jobs[job_id] = {
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'text_length': len(content)
        }

        print(f"[Job {job_id[:8]}] Accepted")

        thread = Thread(
            target=generate_video_task,
            args=(job_id, content, speech_speed, delay),
            daemon=True
        )
        thread.start()

        return jsonify({
            'job_id': job_id,
            'status': 'pending',
            'message': 'Video generation started'
        }), 202

    except Exception as e:
        # Safety unlock if something crashes before thread starts
        if generation_lock.locked():
            generation_lock.release()
        return jsonify({'error': str(e)}), 500

@app.route('/api/status/<job_id>', methods=['GET'])
def get_status(job_id):
    """
    Get job status
    
    Response:
    {
        "status": "pending|completed|failed",
        "file_path": "path/to/video.mp4" (if completed),
        "error": "error message" (if failed)
    }
    """
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = jobs[job_id]
    return jsonify(job), 200


@app.route('/api/videos/<video_id>', methods=['GET'])
def get_video(video_id):
    """
    Download or stream video
    """
    video_path = UPLOAD_FOLDER / f"{video_id}.mp4"
    
    if not video_path.exists():
        print(f"❌ Video not found: {video_path}")
        return jsonify({'error': f'Video not found: {video_id}'}), 404
    
    try:
        return send_file(
            str(video_path),
            mimetype='video/mp4',
            as_attachment=request.args.get('download', False),
            download_name=f"generated_{video_id[:8]}.mp4"
        )
    except Exception as e:
        print(f"❌ Error sending video: {str(e)}")
        return jsonify({'error': f'Error serving video: {str(e)}'}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200


@app.route('/api/cleanup', methods=['POST'])
def cleanup_old_files():
    """Cleanup old video files (admin endpoint)"""
    import time
    cutoff_time = time.time() - (24 * 3600)  # 24 hours
    count = 0
    
    for file in UPLOAD_FOLDER.glob('*.mp4'):
        if os.path.getmtime(file) < cutoff_time:
            os.remove(file)
            count += 1
    
    return jsonify({'cleaned': count}), 200


# ============ ERROR HANDLERS ============

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 Chinese TTS Video Generator")
    print("="*50)
    print(f"📁 Upload folder: {UPLOAD_FOLDER.absolute()}")
    print(f"🌍 Server: http://{app.config['HOST']}:{app.config['PORT']}")
    print(f"🔧 Debug: {app.config['DEBUG']}")
    print(f"📝 Environment: {app.config.get('FLASK_ENV', 'development')}")
    print("="*50 + "\n")
    
    app.run(
        debug=app.config['DEBUG'],
        host=app.config['HOST'],
        port=app.config['PORT']
    )
