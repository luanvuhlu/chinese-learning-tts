"""
Refactored TTS Video Generator Module
Extracted from create-video.py for API use
"""
import os
import subprocess
import wave
import contextlib
import numpy as np
import soundfile as sf
import sherpa_onnx
from pypinyin import pinyin, Style
import re

# --- CONFIGURATION ---
BG_IMAGE = "background.png"
FONT_PATH = "models/msyh.ttc"


def transform_data(multi_line_text):
    """Convert multi-line text to list of dicts with Chinese and Pinyin"""
    chinese_sentences = [i.strip() for i in multi_line_text.split('\n') if i.strip()]
    data_list = []
    for sentence in chinese_sentences:
        py_list = pinyin(sentence, style=Style.TONE)
        py_string = " ".join([item[0] for item in py_list])
        data_list.append({"zh": sentence, "py": py_string})
    return data_list


def create_pinyin_only(text_content):
    """
    Generate pinyin-only text from Chinese text
    
    Args:
        text_content: Multi-line Chinese text
    
    Returns:
        String containing only pinyin text, one line per sentence
    """
    try:
        data = transform_data(text_content)
        if not data:
            raise ValueError("No valid Chinese sentences found in text")
        
        pinyin_lines = []
        for item in data:
            pinyin_lines.append(item['py'])
        
        return "\n".join(pinyin_lines)
        
    except Exception as e:
        raise


def count_chinese_chars_only(text):
    """Count only Chinese characters in the text"""
    return sum(1 for _ in re.finditer(r'[\u4e00-\u9fff]', text))


def create_tts():
    """Initialize Matcha-TTS model"""
    config = sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(
            matcha=sherpa_onnx.OfflineTtsMatchaModelConfig(
                acoustic_model="models/matcha-icefall-zh-baker/model-steps-3.onnx",
                vocoder="models/vocos-22khz-univ.onnx",
                lexicon="models/matcha-icefall-zh-baker/lexicon.txt",
                tokens="models/matcha-icefall-zh-baker/tokens.txt",
            ),
            num_threads=2,
            debug=False,
        ),
        max_num_sentences=1,
        rule_fsts="models/matcha-icefall-zh-baker/phone.fst,models/matcha-icefall-zh-baker/date.fst,models/matcha-icefall-zh-baker/number.fst",
    )
    return sherpa_onnx.OfflineTts(config)


def create_silence(duration, samplerate, output_path):
    """Create silent WAV file with given duration"""
    samples = np.zeros(int(duration * samplerate), dtype=np.float32)
    sf.write(output_path, samples, samplerate)


def escape_ffmpeg_text(text):
    """Escape special characters for FFmpeg"""
    return text.replace("'", "\\'").replace(":", "\\:")


def escape_speaker_text(text):
    """Extract speech content after speaker name (if exists)"""
    for index, char in enumerate(text):
        if char == ':' or char == '：':
            for i in range(index+1, len(text)):
                if text[i] != ' ' and text[i] != ' ':
                    return text[i:]
    return text


def create_ffmpeg_script(subtitle_configs, subtitle_color="black", subtitle_size=100, show_pinyin=True):
    """
    Create FFmpeg filter complex script for subtitles
    
    Args:
        subtitle_configs: List of subtitle timing configs
        subtitle_color: Text color (e.g., 'black', 'white', or hex '#FFFFFF')
        subtitle_size: Font size for Chinese text (Pinyin will be 35% of this size)
        show_pinyin: Whether to render pinyin above Chinese text
    """
    filter_script_path = "filter_complex.txt"
    safe_font = FONT_PATH.replace("\\", "/")
    
    # Validate and normalize color
    valid_colors = {
        'black', 'white', 'red', 'green', 'blue', 'yellow', 'cyan', 'magenta',
        'gray', 'grey', 'orange', 'purple', 'pink', 'brown', 'navy', 'teal'
    }
    if subtitle_color.lower() not in valid_colors and not (subtitle_color.startswith('#') and len(subtitle_color) == 7):
        subtitle_color = 'black'
    
    # Validate size (20-200)
    try:
        subtitle_size = max(20, min(200, int(subtitle_size)))
    except (ValueError, TypeError):
        subtitle_size = 100
    
    pinyin_size = max(10, int(subtitle_size * 0.35))
    
    filter_parts = []
    for conf in subtitle_configs:
        zh_esc = escape_ffmpeg_text(conf['zh'])
        py_esc = escape_ffmpeg_text(conf['py'])
        start, end = conf['start'], conf['end']

        if show_pinyin:
            # Pinyin subtitle
            filter_parts.append(
                f"drawtext=fontfile='{safe_font}':text='{py_esc}':fontcolor={subtitle_color}:fontsize={pinyin_size}:"
                f"x=(w-text_w)/2:y=h/2-100:enable='between(t,{start},{end})'"
            )
            # Chinese characters subtitle
            filter_parts.append(
                f"drawtext=fontfile='{safe_font}':text='{zh_esc}':fontcolor={subtitle_color}:fontsize={subtitle_size}:"
                f"x=(w-text_w)/2:y=h/2-55:enable='between(t,{start},{end})'"
            )
        else:
            # Chinese characters subtitle only
            filter_parts.append(
                f"drawtext=fontfile='{safe_font}':text='{zh_esc}':fontcolor={subtitle_color}:fontsize={subtitle_size}:"
                f"x=(w-text_w)/2:y=(h-text_h)/2:enable='between(t,{start},{end})'"
            )

    with open(filter_script_path, "w", encoding="utf-8") as f:
        f.write(",".join(filter_parts))
    return filter_script_path


def generate_audio(data, audio_segments, delay, subtitle_configs, concat_list, speech_speed, output_audio):
    """Generate audio segments with specified speech speed"""
    tts = create_tts()
    current_time = 0.0
    num_sentences = len(data)
    
    for i, item in enumerate(data):
        # 1. Create speech audio
        speech_path = f"temp_speech_{i}.wav"
        audio = tts.generate(escape_speaker_text(item['zh']), sid=0, speed=speech_speed)
        sf.write(speech_path, audio.samples, samplerate=audio.sample_rate)
        
        speech_dur = len(audio.samples) / audio.sample_rate
        
        # 2. Append speech FIRST (no delay at start)
        audio_segments.append(speech_path)

        # 3. Create silence pause only if not single sentence and not the last sentence
        silence_dur = 0
        if num_sentences > 1 and i < num_sentences - 1:
            # silence_dur = count_chinese_chars_only(escape_speaker_text(item['zh'])) * MS_PER_CHAR
            silence_dur = delay
            silence_path = f"temp_silence_{i}.wav"
            create_silence(silence_dur, audio.sample_rate, silence_path)
            audio_segments.append(silence_path)

        # Store subtitle timing - include silence duration so subtitle stays visible during pause
        subtitle_configs.append({
            "start": current_time,
            "end": current_time + speech_dur + silence_dur, 
            "zh": item['zh'],
            "py": item['py']
        })
        
        # Update time for next sentence
        current_time += (speech_dur + silence_dur)
        
        duration_display = speech_dur + silence_dur
        print(f"Done sentence {i+1}: {item['zh']} (Duration: {duration_display:.2f}s)")
    
    print("🎵 Concatenating audio segments...")
    with open(concat_list, "w", encoding="utf-8") as f:
        for p in audio_segments:
            f.write(f"file '{p}'\n")
            
    # Run ffmpeg concat command
    concat_cmd = f"ffmpeg -y -f concat -safe 0 -i {concat_list} -c copy {output_audio}"
    result = subprocess.run(concat_cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg concat failed: {result.stderr}")


def create_audio_only(text_content, speech_speed=0.9, delay=2.0, output_path="data/final_audio.mp3"):
    """
    Generate audio-only (MP3) from text with specified parameters
    
    Args:
        text_content: Multi-line Chinese text
        speech_speed: Speech speed (0.1 to 2.0)
        delay: Delay between sentences (0 to 10)
        output_path: Path to save output MP3 file
    
    Returns:
        Path to generated MP3 file
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        data = transform_data(text_content)
        if not data:
            raise ValueError("No valid Chinese sentences found in text")
        
        audio_segments = []
        subtitle_configs = []
        
        print(f"🚀 Starting to create audio {len(data)} sentences...")
        
        concat_list = "concat_list.txt"
        output_wav = output_path.replace('.mp3', '.wav')
        
        # Generate audio
        generate_audio(data, audio_segments, delay, subtitle_configs, concat_list, speech_speed, output_wav)
        
        # Verify audio file was created
        if not os.path.exists(output_wav):
            raise RuntimeError(f"Audio file was not created: {output_wav}")
        
        print("🎵 Converting to MP3...")
        
        # Convert WAV to MP3 using FFmpeg
        cmd = [
            'ffmpeg', '-y',
            '-i', output_wav,
            '-q:a', '9',  # Quality: 0-9 (9 is highest compression, lowest quality)
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg MP3 conversion failed: {result.stderr}")
        
        # Cleanup temp files
        for p in audio_segments:
            if os.path.exists(p):
                os.remove(p)
        if os.path.exists(concat_list):
            os.remove(concat_list)
        if os.path.exists(output_wav):
            os.remove(output_wav)
        
        print(f"✅ Audio complete! MP3 saved at: {output_path}")
        return output_path
        
    except Exception as e:
        # Cleanup on error
        for f in ["concat_list.txt", "filter_complex.txt"]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass
        raise
        
def create_video(text_content, speech_speed=0.9, delay=2.0, output_path="data/final_video.mp4", bg_image=None, subtitle_color="black", subtitle_size=100, show_pinyin=True):
    """
    Generate video from text with specified parameters
    
    Args:
        text_content: Multi-line Chinese text
        speech_speed: Speech speed (0.1 to 2.0)
        delay: Delay between sentences (0 to 10)
        output_path: Path to save output video
        bg_image: Optional path to background image (uses default if None)
        subtitle_color: Subtitle text color ('black', 'white', 'red', etc. or hex '#FFFFFF')
        subtitle_size: Subtitle font size (20-200)
    
    Returns:
        Path to generated video file
    """
    # Use provided background image or default
    background_image = bg_image if bg_image and os.path.exists(bg_image) else BG_IMAGE
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        data = transform_data(text_content)
        if not data:
            raise ValueError("No valid Chinese sentences found in text")
        
        audio_segments = []
        subtitle_configs = []
        
        print(f"🚀 Starting to create {len(data)} sentences...")
        
        concat_list = "concat_list.txt"
        output_audio = output_path.replace('.mp4', '.wav')
        
        # Generate audio with output_audio path
        generate_audio(data, audio_segments, delay, subtitle_configs, concat_list, speech_speed, output_audio)
        
        # Verify audio file was created
        if not os.path.exists(output_audio):
            raise RuntimeError(f"Audio file was not created: {output_audio}")
        
        filter_script_path = create_ffmpeg_script(subtitle_configs, subtitle_color, subtitle_size, show_pinyin)
        print("🎬 Rendering final video...")
        
        # Render video with specified background image
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1', '-i', background_image,
            '-i', output_audio,
            '-filter_complex_script', filter_script_path,
            '-c:v', 'libx264', '-preset', 'ultrafast',
            '-c:a', 'aac', '-b:a', '192k',
            '-shortest', output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg video rendering failed: {result.stderr}")

        # Cleanup temp files
        for p in audio_segments:
            if os.path.exists(p):
                os.remove(p)
        if os.path.exists(concat_list):
            os.remove(concat_list)
        if os.path.exists(filter_script_path):
            os.remove(filter_script_path)
        if os.path.exists(output_audio):
            os.remove(output_audio)
        
        print(f"✅ Complete! Video saved at: {output_path}")
        return output_path
        
    except Exception as e:
        # Cleanup on error
        for f in ["concat_list.txt", "filter_complex.txt"]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass
        raise


if __name__ == "__main__":
    # Test with sample text
    sample_text = """大卫：今天天气怎么样？
李军：今天晴天，很暖和。"""
    create_video(sample_text)
