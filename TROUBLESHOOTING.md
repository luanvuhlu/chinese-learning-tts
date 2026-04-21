# 🔧 Troubleshooting Guide

## Common Issues and Solutions

### 1. Installation Issues

#### "Python 3.13 not found"
**Symptoms:** `ModuleNotFoundError: No module named 'xyz'` or version error

**Solutions:**
1. Check Python version:
   ```bash
   python --version
   python3 --version
   ```
2. Install Python 3.13+:
   - Windows: https://www.python.org/downloads/
   - macOS: `brew install python@3.13`
   - Linux: `sudo apt-get install python3.13`

3. Create virtual environment with specific version:
   ```bash
   python3.13 -m venv .venv
   ```

---

#### "FFmpeg not found"
**Symptoms:** `FileNotFoundError: ffmpeg` or video fails to generate

**Solutions:**
1. Check if installed:
   ```bash
   ffmpeg -version
   ffmpeg -encoders
   ```

2. Install FFmpeg:
   
   **Windows:**
   ```bash
   choco install ffmpeg
   # Or download from https://ffmpeg.org
   ```
   
   **macOS:**
   ```bash
   brew install ffmpeg
   ```
   
   **Linux (Ubuntu/Debian):**
   ```bash
   sudo apt-get install ffmpeg
   ```
   
   **Linux (Fedora/CentOS):**
   ```bash
   sudo dnf install ffmpeg
   ```

3. Add to PATH if needed:
   - Windows: Check System Properties > Environment Variables
   - macOS/Linux: Check `echo $PATH` includes ffmpeg location

4. Restart terminal and application after installation

---

#### "Dependency installation fails"
**Symptoms:** `pip install` fails with error

**Solutions:**
1. Upgrade pip:
   ```bash
   python -m pip install --upgrade pip
   ```

2. Use specific requirements file:
   ```bash
   pip install -r requirements.txt
   ```

3. If using pyproject.toml:
   ```bash
   pip install -e .
   ```

4. Install dependencies individually:
   ```bash
   pip install Flask==3.0.0 Flask-CORS==4.0.0 python-dotenv==1.0.0
   pip install sherpa-onnx==1.12.39 sherpa-onnx-bin==1.12.39
   ```

---

### 2. Model Files Issues

#### "Models not found"
**Symptoms:** `FileNotFoundError: models/...` or TTS fails

**Required Files:**
```
models/
├── msyh.ttc
├── vocos-22khz-univ.onnx
├── vocos_24khz.onnx
└── matcha-icefall-zh-baker/
    ├── model-steps-3.onnx
    ├── lexicon.txt
    ├── tokens.txt
    ├── phone.fst
    ├── date.fst
    ├── number.fst
    └── dict/ (with various .utf8 files)
```

**Solution:**
1. Verify all files exist:
   ```bash
   ls -la models/
   ls -la models/matcha-icefall-zh-baker/
   ```

2. If missing, download from:
   - Matcha-TTS: https://huggingface.co/KsanL/icefall-zh-baker
   - Font: Microsoft YaHei from system or download separately

3. Place files in correct directory:
   - Copy to `models/` folder
   - Maintain subdirectory structure

---

### 3. Server Start Issues

#### "Port 5000 already in use"
**Symptoms:** `OSError: [Errno 48] Address already in use` or similar

**Solutions:**
1. Find process using port:
   ```bash
   # Windows
   netstat -ano | findstr :5000
   taskkill /PID <PID> /F
   
   # macOS/Linux
   lsof -i :5000
   kill -9 <PID>
   ```

2. Change port in `.env`:
   ```bash
   PORT=5001
   ```

3. Or change in code (`app.py`):
   ```python
   if __name__ == '__main__':
       app.run(port=5001)
   ```

---

#### "ModuleNotFoundError: No module named 'flask'"
**Symptoms:** Flask not found when running app

**Solutions:**
1. Verify virtual environment activated:
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```

2. Install Flask:
   ```bash
   pip install Flask==3.0.0
   ```

3. Use run script (handles activation):
   ```bash
   # Windows
   run.bat
   
   # macOS/Linux
   ./run.sh
   ```

---

#### "Cannot bind to address"
**Symptoms:** `OSError: Cannot bind address` error

**Solutions:**
1. Use 0.0.0.0:5000 instead of localhost
2. Change `HOST` in `.env`:
   ```bash
   HOST=127.0.0.1
   PORT=5000
   ```

3. Or in `app.py`:
   ```python
   app.run(host='127.0.0.1', port=5000)
   ```

---

### 4. Web UI Issues

#### "Cannot access http://localhost:5000"
**Symptoms:** Browser shows "Cannot connect" or "Connection refused"

**Solutions:**
1. Verify server is running:
   - Check terminal output
   - Look for "Running on http://..."

2. Check firewall:
   - Windows: Allow Python through firewall
   - macOS: System Preferences > Security & Privacy
   - Linux: `sudo ufw allow 5000`

3. Use correct address:
   - `http://localhost:5000` (not https)
   - `http://127.0.0.1:5000` (alternative)
   - If on network: `http://<your-ip>:5000`

4. Check if port is different:
   - Check `.env` for `PORT` setting
   - Check server output for actual port

---

#### "UI not loading (blank page)"
**Symptoms:** Page loads but shows nothing

**Solutions:**
1. Hard refresh browser:
   - Chrome/Firefox: Ctrl+Shift+R
   - Safari: Cmd+Shift+R
   - Edge: Ctrl+Shift+Delete

2. Check browser console (F12 or right-click > Inspect):
   - Look for JavaScript errors
   - Check Network tab for failed requests

3. Verify static files exist:
   ```bash
   ls -la static/
   ls -la templates/
   ```

4. Check server logs for errors

---

#### "Sliders or buttons not working"
**Symptoms:** UI displays but interactions don't work

**Solutions:**
1. Check browser console for errors (F12)
2. Verify JavaScript enabled
3. Try different browser
4. Clear browser cache
5. Check static/script.js file exists and loads

---

### 5. Video Generation Issues

#### "Video generation fails silently"
**Symptoms:** Job status shows "failed" with no error message

**Solutions:**
1. Check browser console (F12) for error details
2. Check server terminal for error output
3. Try with shorter text first (10-20 characters)
4. Verify:
   - FFmpeg is installed and working
   - Models are present
   - Disk space available (need ~500MB free)

---

#### "Generation takes very long time"
**Symptoms:** Video generation seems stuck or frozen

**Solutions:**
1. Check if it's actually processing:
   - CPU usage (Task Manager/Activity Monitor)
   - Check system resources

2. Expected times:
   - Short text (100 chars): 1-2 minutes
   - Medium text (500 chars): 2-4 minutes
   - Long text (1000 chars): 4-5 minutes

3. Optimize performance:
   - Use default speech speed (0.9x)
   - Try shorter text
   - Close other applications
   - Restart server

4. Check server logs for:
   - TTS processing messages
   - Audio generation messages
   - FFmpeg output

---

#### "Generation fails with FFmpeg error"
**Symptoms:** `FFmpeg error` message or subprocess error

**Solutions:**
1. Verify FFmpeg works:
   ```bash
   ffmpeg -version
   ffmpeg -codecs | grep libx264
   ```

2. Check background image exists:
   ```bash
   ls -la background.png
   ```

3. Check FFmpeg codec availability:
   - Windows: May need codec installation
   - macOS/Linux: Reinstall FFmpeg

4. Try manually (debug):
   ```bash
   ffmpeg -loop 1 -i background.png -i audio.wav -c:v libx264 -c:a aac output.mp4
   ```

---

#### "Character encoding issues (garbled text)"
**Symptoms:** Chinese characters appear as squares or gibberish

**Solutions:**
1. Verify font file:
   ```bash
   ls -la models/msyh.ttc
   ```

2. Check UTF-8 encoding:
   - Ensure text is UTF-8
   - HTML should have `<meta charset="UTF-8">`

3. Reinstall Windows fonts:
   - Ensure Microsoft YaHei is installed
   - Or use system font

---

### 6. Performance Issues

#### "Server is slow"
**Symptoms:** UI response slow or generation very slow

**Solutions:**
1. Check system resources:
   - CPU usage
   - Memory usage
   - Disk space

2. Check for bottlenecks:
   - TTS generation (CPU-intensive)
   - FFmpeg video rendering (CPU-intensive)
   - Disk I/O (check disk speed)

3. Optimize:
   - Close unnecessary applications
   - Increase RAM available
   - Use SSD instead of HDD
   - Single-thread to completion

---

#### "Disk space warning"
**Symptoms:** Out of disk space errors

**Solutions:**
1. Clean up old videos:
   ```bash
   curl -X POST http://localhost:5000/api/cleanup
   ```

2. Manually delete:
   ```bash
   rm -rf uploads/*.mp4
   ```

3. Check disk space:
   ```bash
   # Windows
   dir C:\
   
   # macOS/Linux
   df -h
   ```

4. Need at least 500MB free for generation

---

### 7. Browser Compatibility

#### "Video player not working"
**Symptoms:** Video doesn't play or no controls shown

**Solutions:**
1. Check browser supports HTML5:
   - Chrome 9+
   - Firefox 25+
   - Safari 6+
   - Edge 12+

2. Check video file:
   ```bash
   ls -la uploads/
   ffmpeg -i uploads/video.mp4
   ```

3. Try different browser

4. Check CORS settings (if deployed)

---

#### "Sliders not smooth on mobile"
**Symptoms:** Slider jumps or doesn't respond smoothly on phone

**Solutions:**
1. Try different mobile browser
2. Close other applications
3. Try portrait/landscape orientation
4. Clear browser cache

---

### 8. API Issues

#### "API returns 400 Bad Request"
**Symptoms:** `{"error": "..."}` response

**Common errors:**
- Content length > 1000 characters
- Speech speed not 0.1-2.0
- Delay not 0-1
- Missing required fields

**Solution:**
Verify request:
```javascript
console.log({
  contentLength: content.length,
  speechSpeed: typeof speechSpeed, // should be number 0.1-2.0
  delay: typeof delay,  // should be number 0-1
  content: content.trim().length > 0  // should be true
});
```

---

#### "API returns 500 Server Error"
**Symptoms:** `{"error": "Server error: ..."}` response

**Solutions:**
1. Check server terminal for detailed error
2. Verify dependencies installed
3. Check models exist
4. Verify disk space available
5. Restart server

---

#### "Job status returns "pending" forever"
**Symptoms:** Status always pending, never completes

**Solutions:**
1. Check server terminal for processing messages
2. Monitor CPU/memory usage
3. Check if text causes infinite loop (try shorter text)
4. Restart server
5. Check disk space

---

### 9. Database/Storage Issues

#### "Uploads folder not created"
**Symptoms:** FileNotFoundError or "uploads directory missing"

**Solution:**
1. Create manually:
   ```bash
   mkdir uploads
   ```

2. Verify permissions:
   ```bash
   chmod 755 uploads
   ```

---

#### "Cannot delete old videos"
**Symptoms:** Cleanup endpoint fails

**Solutions:**
1. Check permissions:
   ```bash
   ls -la uploads/
   chmod 755 uploads/
   chmod 644 uploads/*.mp4
   ```

2. Verify no processes using files:
   - Close any video players
   - Check open file handles

---

### 10. Development Issues

#### "Changes not reflected after code edit"
**Symptoms:** Modified code doesn't take effect

**Solutions:**
1. Restart Flask server (stop and start)
2. Verify FLASK_DEBUG=True in `.env`
3. Check syntax errors (Python will fail)
4. Hard refresh browser (Ctrl+Shift+R)
5. Clear static file cache

---

#### "Template not updating"
**Symptoms:** HTML changes don't appear

**Solutions:**
1. Verify file saved
2. Check file path correct
3. Hard refresh browser
4. Restart server
5. Check Flask can read file:
   ```bash
   cat templates/index.html
   ```

---

## Debugging Tips

### Enable Verbose Logging
```bash
export FLASK_ENV=development
export FLASK_DEBUG=True
python app.py
```

### Check Running Processes
```bash
# Windows
Get-Process | grep -i python

# macOS/Linux
ps aux | grep python
```

### Monitor System Resources
```bash
# Windows
Get-Process | Sort-Object -Descending CPU | Select -First 5

# macOS
top -n 1

# Linux
top -b -n 1
```

### View Application Logs
```bash
# Last 50 lines
tail -50 app.log

# Follow in real-time
tail -f app.log
```

---

## Getting Help

1. **Check Documentation:**
   - [README.md](README.md)
   - [QUICKSTART.md](QUICKSTART.md)
   - [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

2. **Browser Console (F12):**
   - Check for JavaScript errors
   - Review Network requests
   - Look at server response

3. **Server Terminal:**
   - Watch for error messages
   - Monitor API requests
   - Track background task progress

4. **System Diagnostics:**
   - Check resource usage
   - Verify installation
   - Test dependencies individually

---

## Performance Checklist

- [ ] Python 3.13+ installed
- [ ] FFmpeg installed and in PATH
- [ ] All model files present in `models/`
- [ ] Background image exists
- [ ] At least 500MB disk space free
- [ ] No other services on port 5000
- [ ] Virtual environment activated
- [ ] All dependencies installed
- [ ] Server starts without errors
- [ ] Web UI loads in browser
- [ ] Test generation works

---

**Still stuck? Check the documentation or check browser console for specific error messages!**
