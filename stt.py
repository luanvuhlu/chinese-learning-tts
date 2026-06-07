"""
Speech-to-Text helpers and adapters.

This module provides utilities to convert arbitrary audio files to a 16k mono WAV
and a small adapter that will try to transcribe audio using available engines.

Behavior:
- convert_to_wav: uses ffmpeg to create a 16k mono WAV suitable for most ASR models
- transcribe_file: tries whisper (if installed) first, then falls back to sherpa_onnx if available.

If no supported engine is available it raises a RuntimeError with instructions.
"""
import os
import subprocess
import uuid
import wave
import contextlib
from pathlib import Path
from typing import Dict, Any, List, Optional

SUPPORTED_AUDIO_EXT = {'.wav', '.mp3', '.m4a', '.webm', '.ogg', '.flac', '.aac'}


def convert_to_wav(input_path: str, output_wav: str, sample_rate: int = 16000) -> str:
    """Convert any input audio to a mono PCM WAV with given sample_rate using ffmpeg.

    Raises RuntimeError if ffmpeg fails or is not installed.
    Returns the path to the converted WAV (output_wav).
    """
    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-ac', '1',
        '-ar', str(sample_rate),
        '-sample_fmt', 's16',
        output_wav,
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg conversion failed: {proc.stderr}")
    return output_wav


def _wav_duration(path: str) -> float:
    with contextlib.closing(wave.open(path, 'rb')) as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / float(rate)


def _transcribe_with_whisper(wav_path: str, model_name: str = 'tiny') -> Dict[str, Any]:
    """Transcribe audio using OpenAI Whisper.
    
    Model memory requirements (CPU-only):
    - tiny (39 MB): ~500 MB RAM, 10-30s per minute
    - base (140 MB): ~1 GB RAM, 30-60s per minute
    - small (466 MB): ~1.5-2 GB RAM, 1-2 min per minute
    - medium+ (1.5 GB+): requires 4+ GB RAM
    
    For 2GB RAM servers, use 'tiny' or 'base'.
    """
    try:
        import whisper
    except Exception as e:
        raise RuntimeError('whisper package is not installed. Install with `pip install -U openai-whisper`') from e

    # Allow selecting model via env var
    import os
    model_name = os.getenv('WHISPER_MODEL', model_name)
    model = whisper.load_model(model_name)
    # whisper accepts paths directly
    result = model.transcribe(wav_path, language='zh', verbose=False)
    # result contains 'text' and 'segments' keys
    return {
        'transcript': result.get('text', '').strip(),
        'segments': result.get('segments', []),
        'engine': 'whisper',
    }


def _transcribe_with_sherpa(wav_path: str) -> Dict[str, Any]:
    try:
        import sherpa_onnx
    except Exception as e:
        raise RuntimeError('sherpa_onnx is not installed') from e

    # The exact ASR model files/paths/config may vary by installation. We will
    # look for environment variables pointing to model files. If they are not
    # present, raise an error instructing the user to configure the ASR model.
    model_dir = os.getenv('ASR_MODEL_DIR', '')
    if not model_dir:
        raise RuntimeError('ASR model directory not configured. Set ASR_MODEL_DIR env var to sherpa-onnx ASR model folder')

    # This code attempts to create an OfflineRecognizer if available. The API
    # surface can vary between versions; wrap in try/except to surface a
    # helpful error if the local sherpa_onnx install can't be used.
    try:
        # Create a nominal config; users should set ASR model files in model_dir
        # Example model filenames (may differ): encoder.onnx, decoder.onnx, joiner.onnx, tokens.txt
        encoder = os.path.join(model_dir, 'encoder.onnx')
        decoder = os.path.join(model_dir, 'decoder.onnx')
        joiner = os.path.join(model_dir, 'joiner.onnx')
        tokens = os.path.join(model_dir, 'tokens.txt')

        if not (os.path.exists(encoder) and os.path.exists(decoder) and os.path.exists(joiner) and os.path.exists(tokens)):
            raise RuntimeError(f'Missing sherpa-onnx ASR model files in {model_dir}. Expected encoder/decoder/joiner/tokens')

        model = sherpa_onnx.OfflineRecognizerModelConfig(
            encoder=encoder,
            decoder=decoder,
            joiner=joiner,
            tokens=tokens,
        )

        recognizer_config = sherpa_onnx.OfflineRecognizerConfig(model=model)
        recognizer = sherpa_onnx.OfflineRecognizer(recognizer_config)

        # Read the entire WAV file and run recognition
        # The exact API for feeding audio may differ; attempt a common pattern.
        with open(wav_path, 'rb') as f:
            # Many sherpa_onnx versions expect a numpy array or bytes; try the helper
            results = recognizer.recognize(wav_path)

        # Attempt to normalize results
        transcript = ''
        segments = []
        if isinstance(results, list):
            # Some APIs return a list of segments
            for seg in results:
                text = ''
                if isinstance(seg, dict):
                    text = seg.get('text') or ''
                else:
                    try:
                        text = str(seg)
                    except Exception:
                        text = ''
                transcript += text + ' '
        elif isinstance(results, dict):
            transcript = results.get('text', '')

        return {'transcript': transcript.strip(), 'segments': segments, 'engine': 'sherpa_onnx'}

    except Exception as e:
        raise RuntimeError(f'sherpa_onnx transcription failed: {e}') from e


def transcribe_file(input_audio_path: str, working_dir: str = '.', engine_preference: Optional[List[str]] = None) -> Dict[str, Any]:
    """High-level function to transcribe an input audio file.

    Steps:
    - convert input to 16k mono WAV in a temporary path
    - attempt transcription with available engines (whisper -> sherpa_onnx)
    - return a dict with keys: transcript, segments, duration, engine
    """
    engine_preference = engine_preference or ['whisper', 'sherpa']

    Path(working_dir).mkdir(parents=True, exist_ok=True)
    base = str(uuid.uuid4())
    wav_path = os.path.join(working_dir, f'{base}.wav')

    # Convert
    convert_to_wav(input_audio_path, wav_path)

    duration = _wav_duration(wav_path)

    last_err = None
    for engine in engine_preference:
        try:
            if engine.lower().startswith('whisp'):
                res = _transcribe_with_whisper(wav_path)
            else:
                res = _transcribe_with_sherpa(wav_path)

            res['duration'] = duration
            res['wav_path'] = wav_path
            return res
        except Exception as e:
            last_err = e
            # try next engine
            continue

    # If we reach here, no engine succeeded
    raise RuntimeError(f'No STT engine succeeded. Last error: {last_err}')
