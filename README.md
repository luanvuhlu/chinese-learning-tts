# 🎬 Chinese TTS Video Generator Website

A complete web application for generating videos from Chinese text using Text-to-Speech synthesis. The project includes a Flask API backend and a responsive web UI.

## Features

✨ **Core Functionality**
- Generate videos with Chinese speech synthesis using Matcha-TTS
- Adjustable speech speed (0.1x to 2.0x)
- Configurable pause duration between sentences (0 to 1 second)
- Support for multi-line Chinese text with speaker names
- Real-time video player with download capability

🎨 **User Interface**
- Fully responsive design (mobile, tablet, desktop)
- Modern, intuitive UI with smooth animations
- Real-time character counter
- Live slider value display
- Progress indicator during video generation
- Error handling and user feedback

🔧 **Technical Stack**
- **Backend**: Flask + Python
- **Frontend**: HTML5, CSS3, JavaScript
- **TTS Engine**: Sherpa-ONNX (Matcha-TTS)
- **Video Processing**: FFmpeg

## Project Structure

```
chineses-tts/
├── app.py                    # Flask API server
├── tts_generator.py          # Refactored TTS generation module
├── create-video.py           # Original generation script (preserved)
├── pyproject.toml            # Project dependencies
├── templates/
│   └── index.html            # Main web UI
├── static/
│   ├── style.css             # Responsive styling
│   └── script.js             # Frontend interactivity
├── models/                   # TTS models directory
├── data/                     # Output videos directory
└── uploads/                  # Generated videos storage
```

## Installation

### Prerequisites
- Python 3.13+
- FFmpeg (for video rendering)
- Git

### Setup Steps

1. **Clone the repository**
```bash
cd chineses-tts
```

2. **Create virtual environment**
```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -e .
```

4. **Verify FFmpeg installation**
```bash
ffmpeg -version
```

## Usage

### Running the Web Server

```bash
python app.py
```

The application will be available at: `http://localhost:5000`

### Web UI

1. **Configure Parameters**
   - Adjust speech speed using the slider (0.1x to 2.0x)
   - Set pause duration between sentences (0 to 1 second)
   - Enter Chinese text in the content textarea

2. **Generate Video**
   - Click the "Generate Video" button
   - Wait for the video to be generated (may take a few minutes)
   - The video will appear with a player below

3. **Download or Play**
   - Play the video directly in the browser
   - Download the video using the download button
   - Generate another video or modify parameters

### API Endpoints

#### 1. Generate Video
```
POST /api/generate
Content-Type: application/json

{
  "content": "大卫：你好\n李军：你好",
  "speech_speed": 0.9,
  "delay": 0.2
}

Response (202 Accepted):
{
  "job_id": "uuid-string",
  "status": "pending",
  "message": "Video generation started"
}
```

#### 2. Check Job Status
```
GET /api/status/<job_id>

Response (200 OK):
{
  "status": "pending|completed|failed",
  "file_path": "path/to/video.mp4",  // if completed
  "error": "error message"            // if failed
}
```

#### 3. Download Video
```
GET /api/videos/<job_id>?download=true

Returns: MP4 video file
```

#### 4. Health Check
```
GET /api/health

Response (200 OK):
{
  "status": "healthy"
}
```

## Configuration

### Text Content Validation
- **Maximum length**: 1000 characters
- **Required format**: Multi-line Chinese text
- **Optional format**: `Speaker:Text` (e.g., "大卫：你好")

### Parameter Constraints
- **Speech Speed**: 0.1 to 2.0 (default: 0.9)
- **Delay**: 0 to 1 second (default: 0.2)

### Speech Speed Guide
- `0.1` - Very slow (slow learners, emphasis)
- `0.9` - Natural speed (default, recommended)
- `1.5` - Fast (native speaker pace)
- `2.0` - Very fast (rapid dialogue)

### Delay Guide
- `0` - No pause between sentences
- `0.2` - Brief pause (default, conversational)
- `0.5` - Moderate pause (reading material)
- `1.0` - Long pause (learning material)

## Model Files

The project uses the following models (pre-downloaded):

- **acoustic_model**: `models/matcha-icefall-zh-baker/model-steps-3.onnx`
- **vocoder**: `models/vocos-22khz-univ.onnx`
- **font**: `models/msyh.ttc`

These models are required for TTS operation.

## Responsive Design

The application is fully responsive:

| Device | Breakpoint | Features |
|--------|-----------|----------|
| Mobile | < 480px | Single column, touch-optimized |
| Tablet | 480px - 1024px | Optimized layout, readable text |
| Desktop | > 1024px | Two-column layout, full features |

## Example Usage

Demo Link: [Web UI](http://107.152.32.201:5000/)

### Sample Input
```
大卫：你好，李军。
李军：你好，大卫。今天天气怎么样？
大卫：今天晴天，很暖和。
李军：我们去哪里玩？
大卫：我想去公园。
```

### Result
- Generated MP4 video with:
  - Chinese speech synthesis
  - Character subtitles (pinyin + Chinese)
  - Configurable timing

## Troubleshooting

### Video Generation Fails
1. Check FFmpeg is installed: `ffmpeg -version`
2. Verify model files exist in `models/` directory
3. Check text contains valid Chinese characters
4. Review browser console for error messages

### Slow Generation
- Video generation typically takes 1-5 minutes depending on:
  - Text length
  - System CPU performance
  - Selected speech speed
- Monitor progress in the web UI

### Player Issues
- Ensure browser supports MP4 playback
- Try different browser if issues persist
- Check browser console for errors

## Development

### Adding Features
1. Backend changes: Modify `app.py` or `tts_generator.py`
2. Frontend changes: Update `templates/index.html`, `static/style.css`, or `static/script.js`
3. Test changes locally before deployment

### API Rate Limiting
For production, consider adding:
- Rate limiting per IP
- Job queue management
- Database for job persistence

## Performance Notes

- **Video Generation**: 1-5 minutes per generation (varies by text length)
- **Browser Memory**: Low memory footprint
- **Disk Space**: Approximately 1-10 MB per video
- **Cleanup**: Old videos auto-cleanup after 24 hours

## Deployment

### Local Development
```bash
python app.py  # Runs on http://localhost:5000
```

### Production (with Gunicorn)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker (Optional)
Create a `Dockerfile` for containerization if needed.

## License

This project is open source and available under the MIT License.

## Acknowledgments

- **Sherpa-ONNX**: TTS engine
- **Matcha-TTS**: Acoustic model
- **FFmpeg**: Video processing
- **Flask**: Web framework

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review API documentation
3. Check browser console for error messages
4. Ensure all dependencies are properly installed

## Notes

- The original `create-video.py` is preserved as-is and can still be used independently
- Generated videos are stored in the `uploads/` directory
- All temporary files are automatically cleaned up after video generation
- The application uses in-memory job tracking (suitable for development; use Redis for production)

---

**Happy Video Generation! 🎉**
