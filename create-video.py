import os
import subprocess
import wave
import contextlib
import numpy as np
import soundfile as sf
import sherpa_onnx
from pypinyin import pinyin, Style

# --- CẤU HÌNH ---
BG_IMAGE = "background.png"
OUTPUT_VIDEO = "data/final_video.mp4"
OUTPUT_AUDIO = 'full_audio.wav'
FONT_PATH = "models/msyh.ttc" 
MS_PER_CHAR = 0.3  # Nghỉ 0.3 giây cho mỗi chữ Hán

text = """大卫：李军，你好！
李军：你好，大卫，你今天有课吗？
大卫：有，我上午八点上课。
玛丽：你们去哪儿？
大卫：我们去教学楼。
玛丽：请问，教学楼在哪儿？
李军：教学楼在图书馆东边。
玛丽：谢谢你！
李军：不客气。你是哪个国家人？
玛丽：我是法国人，你呢？
李军：我是中国人，大卫是越南人。
大卫：认识你，我很高兴。
玛丽：我也很高兴。你们学什么专业？
李军：我学国际关系，大卫学汉语。
大卫：玛丽，你有词典吗？
玛丽：有，这本就是我的词典。
大卫：现在几点钟？
李军：现在七点半。
玛丽：时间不多了，我们快去吧！
大卫：好，一会儿见！
""" # ... (các câu còn lại của bạn)

def transform_data(multi_line_text):
    chinese_sentences = [i.strip() for i in multi_line_text.split('\n') if i.strip()]
    data_list = []
    for sentence in chinese_sentences:
        py_list = pinyin(sentence, style=Style.TONE)
        py_string = " ".join([item[0] for item in py_list])
        data_list.append({"zh": sentence, "py": py_string})
    return data_list

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
        silence_dur = len(escape_speaker_text(item['zh'])) * MS_PER_CHAR
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