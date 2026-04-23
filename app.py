"""
Flask API Server for Chinese TTS Video Generation
"""
import os
import uuid
import json
from datetime import datetime
from pathlib import Path
from threading import Thread, Lock
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from config import config
from tts_generator import create_video, create_audio_only
from werkzeug.utils import secure_filename


# Configuration
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config.from_object(config)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file upload
CORS(app)

UPLOAD_FOLDER = config.UPLOAD_FOLDER
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Background images folder
BG_IMAGES_FOLDER = UPLOAD_FOLDER / "backgrounds"
BG_IMAGES_FOLDER.mkdir(exist_ok=True)

# Allowed extensions for background images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'gif'}

MAX_VIDEO_FILES = config.MAX_VIDEO_FILES   # chỉ giữ tối đa 10 file

# In-memory job tracking (in production, use Redis or database)
jobs = {}
generation_lock = Lock()


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def cleanup_excess_files():
    """
    Delete old video/audio files if count exceeds MAX_VIDEO_FILES
    """
    files = list(UPLOAD_FOLDER.glob("*.mp4")) + list(UPLOAD_FOLDER.glob("*.mp3"))

    if MAX_VIDEO_FILES < 0 or len(files) <= MAX_VIDEO_FILES:
        return

    # Sort by modification time (oldest first)
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
    
    # Validate output format
    output_format = data.get('output_format', 'video')
    if output_format not in ['audio', 'video']:
        errors.append("Output format must be 'audio' or 'video'")
    
    # Validate content
    content = data.get('content', '').strip()
    is_valid, msg = validate_content(content)
    if not is_valid:
        errors.append(msg)
    
    return errors if errors else None, content


def generate_audio_task(job_id, text, speech_speed, delay):
    """Background task to generate audio (MP3)"""
    try:
        output_path = UPLOAD_FOLDER / f"{job_id}.mp3"
        print(f"[Job {job_id[:8]}] Starting audio generation...")
        create_audio_only(text, speech_speed, delay, str(output_path))
        # cleanup after creating new file
        cleanup_excess_files()
        
        jobs[job_id] = {
            'status': 'completed',
            'file_path': str(output_path),
            'file_type': 'audio',
            'completed_at': datetime.now().isoformat()
        }
        print(f"[Job {job_id[:8]}] ✅ Audio generation completed")
    except Exception as e:
        error_msg = str(e)
        print(f"[Job {job_id[:8]}] ❌ Error: {error_msg}")
        jobs[job_id] = {
            'status': 'failed',
            'error': error_msg
        }


def generate_video_task(job_id, text, speech_speed, delay, bg_image=None):
    """Background task to generate video (MP4)"""
    try:
        output_path = UPLOAD_FOLDER / f"{job_id}.mp4"
        print(f"[Job {job_id[:8]}] Starting video generation...")
        create_video(text, speech_speed, delay, str(output_path), bg_image)
        # cleanup after creating new file
        cleanup_excess_files()
        
        jobs[job_id] = {
            'status': 'completed',
            'file_path': str(output_path),
            'file_type': 'video',
            'completed_at': datetime.now().isoformat()
        }
        print(f"[Job {job_id[:8]}] ✅ Video generation completed")
        
        # Cleanup uploaded background image after use
        if bg_image and os.path.exists(bg_image):
            try:
                os.remove(bg_image)
                print(f"[Job {job_id[:8]}] 🗑 Cleaned up background image")
            except Exception as e:
                print(f"[Job {job_id[:8]}] ⚠️ Could not delete background image: {e}")
    except Exception as e:
        error_msg = str(e)
        print(f"[Job {job_id[:8]}] ❌ Error: {error_msg}")
        jobs[job_id] = {
            'status': 'failed',
            'error': error_msg
        }
        
        # Cleanup uploaded background image on error
        if bg_image and os.path.exists(bg_image):
            try:
                os.remove(bg_image)
            except:
                pass
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
    Get all videos/audio files in uploads folder

    Response:
    {
        "count": 3,
        "files": [
            {
                "id": "uuid",
                "filename": "uuid.mp4",
                "url": "/api/videos/uuid",
                "file_type": "video",
                "size": 123456,
                "created_at": "2026-04-21T23:10:00"
            }
        ]
    }
    """
    try:
        mp4_files = list(UPLOAD_FOLDER.glob("*.mp4"))
        mp3_files = list(UPLOAD_FOLDER.glob("*.mp3"))
        files = mp4_files + mp3_files

        items = []

        for file in files:
            file_id = file.stem
            
            # Skip files that are still being generated (job is pending/processing)
            if file_id in jobs:
                job = jobs[file_id]
                if job['status'] != 'completed':
                    # File is still being created, skip it
                    continue
            
            stat = file.stat()
            file_type = 'video' if file.suffix == '.mp4' else 'audio'

            items.append({
                "id": file_id,
                "filename": file.name,
                "url": f"/api/videos/{file_id}",
                "file_type": file_type,
                "size": stat.st_size,
                "created_at": int(stat.st_mtime * 1000)  # Unix timestamp in milliseconds
            })

        # Sort by creation time (newest first)
        items.sort(
            key=lambda x: x["created_at"],
            reverse=True
        )

        return jsonify({
            "count": len(items),
            "files": items
        }), 200

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500
        
@app.route('/api/generate', methods=['POST'])
def generate():
    """
    Generate audio or video from text
    
    Request body (multipart/form-data):
    {
        "content": "Chinese text...",
        "speech_speed": 0.9,
        "delay": 0.2,
        "output_format": "video" (or "audio"),
        "background_image": <file> (optional, only for video)
    }
    
    Response:
    {
        "job_id": "uuid",
        "status": "pending",
        "message": "Generation started",
        "output_format": "video" or "audio"
    }
    """
    try:
        # Get form data
        content = request.form.get('content', '').strip()
        output_format = request.form.get('output_format', 'video')
        
        try:
            speech_speed = float(request.form.get('speech_speed', 0.9))
            delay = float(request.form.get('delay', 0.2))
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid speech_speed or delay value'}), 400
        
        # Validate basic parameters
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        if len(content) > 1000:
            return jsonify({'error': 'Content must not exceed 1000 characters'}), 400
        
        if output_format not in ['audio', 'video']:
            return jsonify({'error': 'Output format must be "audio" or "video"'}), 400
        
        if speech_speed < 0.1 or speech_speed > 2.0:
            return jsonify({'error': 'Speech speed must be between 0.1 and 2.0'}), 400
        
        if delay < 0 or delay > 1:
            return jsonify({'error': 'Delay must be between 0 and 1'}), 400
        
        # Handle background image for video
        bg_image_path = None
        if output_format == 'video' and 'background_image' in request.files:
            bg_file = request.files['background_image']
            if bg_file and bg_file.filename:
                if not allowed_file(bg_file.filename):
                    return jsonify({'error': 'Invalid image format. Allowed: png, jpg, jpeg, bmp, gif'}), 400
                
                # Save uploaded background image
                filename = secure_filename(f"bg_{uuid.uuid4()}_{bg_file.filename}")
                bg_image_path = str(BG_IMAGES_FOLDER / filename)
                bg_file.save(bg_image_path)
                print(f"📸 Background image saved: {filename}")
        
        job_id = str(uuid.uuid4())
        
        jobs[job_id] = {
            'status': 'pending',
            'created_at': int(datetime.now().timestamp() * 1000),  # Unix timestamp in milliseconds
            'text_length': len(content),
            'output_format': output_format
        }
        
        print(f"[Job {job_id[:8]}] Queued - Format: {output_format}, Text: {len(content)} chars, Speed: {speech_speed}x, Delay: {delay}s")
        
        # Start appropriate background task
        if output_format == 'audio':
            thread = Thread(
                target=generate_audio_task,
                args=(job_id, content, speech_speed, delay),
                daemon=True
            )
        else:  # video
            thread = Thread(
                target=generate_video_task,
                args=(job_id, content, speech_speed, delay, bg_image_path),
                daemon=True
            )
        
        thread.start()
        
        return jsonify({
            'job_id': job_id,
            'status': 'pending',
            'message': f'{output_format.capitalize()} generation started',
            'output_format': output_format
        }), 202
        
    except Exception as e:
        print(f"❌ API Error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

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
    Download or stream video/audio file
    
    Supports both .mp4 (video) and .mp3 (audio) files
    """
    # Try both mp4 and mp3 extensions
    mp4_path = UPLOAD_FOLDER / f"{video_id}.mp4"
    mp3_path = UPLOAD_FOLDER / f"{video_id}.mp3"
    
    file_path = None
    mime_type = None
    download_ext = None
    
    if mp4_path.exists():
        file_path = mp4_path
        mime_type = 'video/mp4'
        download_ext = '.mp4'
    elif mp3_path.exists():
        file_path = mp3_path
        mime_type = 'audio/mpeg'
        download_ext = '.mp3'
    
    if not file_path:
        print(f"❌ File not found: {video_id} (tried .mp4 and .mp3)")
        return jsonify({'error': f'File not found: {video_id}'}), 404
    
    try:
        return send_file(
            str(file_path),
            mimetype=mime_type,
            as_attachment=request.args.get('download', False),
            download_name=f"generated_{video_id[:8]}{download_ext}"
        )
    except Exception as e:
        print(f"❌ Error serving file: {str(e)}")
        return jsonify({'error': f'Error serving file: {str(e)}'}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200


@app.route('/api/cleanup', methods=['POST'])
def cleanup_old_files():
    """Cleanup old video/audio files (admin endpoint)"""
    import time
    cutoff_time = time.time() - (24 * 3600)  # 24 hours
    count = 0
    
    # Clean up both mp4 and mp3 files
    for file in list(UPLOAD_FOLDER.glob('*.mp4')) + list(UPLOAD_FOLDER.glob('*.mp3')):
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
    print(f"🔧 Debug: {app.config['FLASK_DEBUG']}")
    print(f"📝 Environment: {app.config.get('FLASK_ENV', 'development')}")
    print("="*50 + "\n")
    
    app.run(
        debug=app.config['FLASK_DEBUG'],
        host=app.config['HOST'],
        port=app.config['PORT'],
    )
