import os
import subprocess
import wave
import contextlib
import numpy as np
import soundfile as sf
import sherpa_onnx
from pypinyin import pinyin, Style
import re

# --- CẤU HÌNH ---
BG_IMAGE = "background.png"
OUTPUT_VIDEO = "data/final_video.mp4"
OUTPUT_AUDIO = 'full_audio.wav'
FONT_PATH = "models/msyh.ttc" 
MS_PER_CHAR = 0.3  # Nghỉ 0.3 giây cho mỗi chữ Hán

text = """大卫：今天天气怎么样？
李军：今天晴天，很暖和。
玛丽：我觉得有点儿热。
大卫：下午去哪儿玩儿？
李军：我想去校园北边。
玛丽：那边有图书馆吗？
李军：有，在教学楼旁边。
大卫：我也想去看看。
玛丽：我先去教室上课。
李军：你几点下课？
玛丽：三点半下课。
大卫：下课后去吗？
玛丽：好，我们一起去。
李军：晚上想看电影吗？
大卫：当然，我很喜欢。
玛丽：电影院在哪儿？
李军：学校东边，很近。
大卫：我们坐出租车吧。
玛丽：走路也可以。
李军：我家在附近。
大卫：你家几口人？
李军：爸爸妈妈和妹妹。
玛丽：你爷爷奶奶呢？
李军：他们在北京。
大卫：周末常见他们吗？
李军：不常，可是常打电话。
玛丽：你妹妹喜欢什么？
李军：她喜欢音乐和游泳。
大卫：我喜欢汉语文学。
玛丽：今天真舒服，快走吧。
""" # ... (các câu còn lại của bạn)

def transform_data(multi_line_text):
    chinese_sentences = [i.strip() for i in multi_line_text.split('\n') if i.strip()]
    data_list = []
    for sentence in chinese_sentences:
        py_list = pinyin(sentence, style=Style.TONE)
        py_string = " ".join([item[0] for item in py_list])
        data_list.append({"zh": sentence, "py": py_string})
    return data_list

def count_chinese_chars_only(text):
    return sum(1 for _ in re.finditer(r'[\u4e00-\u9fff]', text))

def create_tts():
    # Giữ nguyên cấu hình Matcha-TTS của bạn
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
    """Tạo file wav im lặng dựa trên duration"""
    samples = np.zeros(int(duration * samplerate), dtype=np.float32)
    sf.write(output_path, samples, samplerate)

def escape_ffmpeg_text(text):
    return text.replace("'", "\\'").replace(":", "\\:")

def create_video():
    data = transform_data(text)
    audio_segments = [] # Lưu danh sách file wav để concat
    subtitle_configs = [] # Lưu timing để viết filter_complex
    
    print(f"🚀 Khởi đầu tạo {len(data)} câu...")

    concat_list = "concat_list.txt"
    generate_audio(data, audio_segments, subtitle_configs, concat_list)
    filter_script_path = create_ffmpeg_script(subtitle_configs)
    print("🎬 Đang render video cuối cùng...")
    subprocess.run(
        [
            'ffmpeg', '-y',
            '-loop', '1', '-i', BG_IMAGE,
            '-i', OUTPUT_AUDIO,
            '-filter_complex_script', filter_script_path,
            '-c:v', 'libx264', '-preset', 'ultrafast',
            '-c:a', 'aac', '-b:a', '192k',
            '-shortest', OUTPUT_VIDEO
        ]
    )

    # 6. Dọn dẹp
    for p in audio_segments:
        if os.path.exists(p): os.remove(p)
    os.remove(concat_list)
    os.remove(filter_script_path)
    os.remove(OUTPUT_AUDIO)
    print(f"✅ Hoàn thành! Video lưu tại: {OUTPUT_VIDEO}")
    

def create_ffmpeg_script(subtitle_configs):
    filter_script_path = "filter_complex.txt"
    safe_font = FONT_PATH.replace("\\", "/")
    
    filter_parts = []
    for conf in subtitle_configs:
        zh_esc = escape_ffmpeg_text(conf['zh'])
        py_esc = escape_ffmpeg_text(conf['py'])
        start, end = conf['start'], conf['end']
        
        # Pinyin
        filter_parts.append(
            f"drawtext=fontfile='{safe_font}':text='{py_esc}':fontcolor=black:fontsize=35:"
            f"x=(w-text_w)/2:y=h/2-100:enable='between(t,{start},{end})'"
        )
        # Chữ Hán
        filter_parts.append(
            f"drawtext=fontfile='{safe_font}':text='{zh_esc}':fontcolor=black:fontsize=100:"
            f"x=(w-text_w)/2:y=h/2-55:enable='between(t,{start},{end})'"
        )

    with open(filter_script_path, "w", encoding="utf-8") as f:
        f.write(",".join(filter_parts))
    return filter_script_path

def escape_speaker_text(text):
    for index, char in enumerate(text):
        if char == ':' or char == '：':
            for i in range(index+1, len(text)):
                if text[i] != ' ' and text[i] != ' ':
                    return text[i:]
    return text

def generate_audio(data, audio_segments, subtitle_configs, concat_list):
    tts = create_tts()
    current_time = 0.0
    for i, item in enumerate(data):
        # 1. Tạo audio tiếng nói
        speech_path = f"temp_speech_{i}.wav"
        audio = tts.generate(escape_speaker_text(item['zh']), sid=0, speed=0.9)
        sf.write(speech_path, audio.samples, samplerate=audio.sample_rate)
        
        speech_dur = len(audio.samples) / audio.sample_rate
        
        # 2. Tính toán thời gian nghỉ
        silence_dur = count_chinese_chars_only(escape_speaker_text(item['zh'])) * MS_PER_CHAR
        silence_path = f"temp_silence_{i}.wav"
        create_silence(silence_dur, audio.sample_rate, silence_path)

        # --- ĐIỀU CHỈNH QUAN TRỌNG Ở ĐÂY ---
        # "end" bây giờ bao gồm cả speech_dur và silence_dur
        subtitle_configs.append({
            "start": current_time,
            "end": current_time + speech_dur + silence_dur, 
            "zh": item['zh'],
            "py": item['py']
        })
        # ----------------------------------
        
        audio_segments.append(speech_path)
        audio_segments.append(silence_path)
        
        # Cập nhật current_time cho câu kế tiếp
        current_time += (speech_dur + silence_dur)
        
        print(f"Done câu {i+1}: {item['zh']} (Tổng hiện hình: {speech_dur + silence_dur:.2f}s)")
    with open(concat_list, "w", encoding="utf-8") as f:
        for p in audio_segments:
            f.write(f"file '{p}'\n")
            
    subprocess.run(f"ffmpeg -y -f concat -safe 0 -i {concat_list} -c copy {OUTPUT_AUDIO}", shell=True)

if __name__ == "__main__":
    create_video()