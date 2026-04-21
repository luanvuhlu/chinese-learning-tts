# Quick Start Guide

## ⚡ Get Running in 5 Minutes

### Windows Users

1. **Run the startup script:**
   ```bash
   run.bat
   ```
   This will automatically:
   - Create a virtual environment
   - Install all dependencies
   - Start the Flask server

2. **Open your browser:**
   ```
   http://localhost:5000
   ```

3. **Start generating videos!**

### macOS / Linux Users

1. **Make the script executable:**
   ```bash
   chmod +x run.sh
   ```

2. **Run the startup script:**
   ```bash
   ./run.sh
   ```

3. **Open your browser:**
   ```
   http://localhost:5000
   ```

4. **Start generating videos!**

---

## 📋 Prerequisites

- ✅ Python 3.13 or higher
- ✅ FFmpeg installed
- ✅ 2GB+ disk space for models

### Installing FFmpeg

**Windows:**
```bash
# Using Chocolatey
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

---

## 🎯 First Video Generation

1. Enter Chinese text in the content area:
   ```
   大卫：你好
   李军：你好
   ```

2. Adjust sliders (optional):
   - **Speech Speed**: 0.9x (normal)
   - **Delay**: 0.2s (between sentences)

3. Click **"Generate Video"**

4. Wait for generation (1-5 minutes)

5. Play, download, or generate another!

---

## 🔧 Troubleshooting

### "FFmpeg not found"
- Install FFmpeg
- Restart the application
- Or use `ffmpeg -version` to verify installation

### "Models not found"
- Ensure `models/` directory exists with these files:
  - `matcha-icefall-zh-baker/model-steps-3.onnx`
  - `vocos-22khz-univ.onnx`
  - `msyh.ttc`

### Video generation fails
- Check browser console (F12) for errors
- Ensure valid Chinese characters in text
- Try with shorter text first
- Check disk space (need ~500MB free)

### Port 5000 already in use
Edit `app.py` and change:
```python
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)  # Changed to 5001
```

---

## 📱 Using Different Devices

The application automatically adapts to:
- 📱 **Mobile phones** - Single column layout
- 📱 **Tablets** - Optimized 2-column layout
- 🖥️ **Desktops** - Full-featured layout

All work perfectly with touch or mouse input.

---

## 💡 Tips & Tricks

### Best Speech Speed Settings
- **Slow learning**: 0.5x - 0.7x
- **Natural (recommended)**: 0.9x
- **Fast native**: 1.2x - 1.5x
- **Very fast**: 1.8x - 2.0x

### Formatting Text
```
大卫：你好，李军。
李军：你好，大卫。
玛丽：大家好。

大卫：今天天气怎么样？
```
- Use speaker names with `:` or `：`
- Add line breaks between sentences
- Max 1000 characters total

### Performance Tips
- Use speaker names (helps with audio separation)
- Avoid excessive punctuation
- Keep sentences under 20 characters each
- Generate during off-peak hours for faster processing

---

## 🔗 Useful Links

- **Main Page**: http://localhost:5000
- **API Health Check**: http://localhost:5000/api/health
- **Documentation**: See README.md

---

## 🚀 Next Steps

1. ✅ Generate your first video
2. 📖 Read the [README.md](README.md) for detailed documentation
3. 🔌 Explore the [API Endpoints](README.md#api-endpoints)
4. 🎨 Customize the UI by editing `static/style.css`
5. 🚀 Deploy to production when ready

---

## 📞 Support

- Check the [README.md](README.md#troubleshooting) troubleshooting section
- Review browser console (F12) for error messages
- Verify all prerequisites are installed
- Check that models are present in the `models/` directory

---

**Enjoy! 🎬🎉**
