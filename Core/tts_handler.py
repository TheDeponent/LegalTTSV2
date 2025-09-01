
# ============================================================================
# tts_handler.py - Orpheus TTS Handler for LegalTTSV2 (Gradio Edition)
#
# Provides generate_speech(), which sends text to the Orpheus TTS API and saves the result as a WAV file.
# Designed for use with the Gradio-based pipeline. Supports progress_callback for real-time progress bar updates.
# ============================================================================


import os
import requests
import json
import uuid
from dotenv import load_dotenv
from Core.llm_handler import log

load_dotenv()
TTS_ENDPOINT = os.getenv("TTS_ENDPOINT", "http://localhost:5005/v1/audio/speech")


def generate_speech(text, voice="tara", progress_callback=None):
    """
    Generate speech from text using the Orpheus TTS API and save as a WAV file.
    Designed for use with the Gradio pipeline. Reports progress via progress_callback (0-100).
    Returns the path to the generated WAV file, or None on error.
    """
    url = TTS_ENDPOINT
    headers = {"Content-Type": "application/json"}
    payload = {
        "input": text,
        "model": "orpheus-tts",
        "voice": voice.lower(),
        "response_format": "wav",
        "speed": 1
    }
    try:
        outputs_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs"))
        os.makedirs(outputs_dir, exist_ok=True)
        filename = f"tts_{uuid.uuid4().hex}.wav"
        output_path = os.path.join(outputs_dir, filename)

        log(f"Requesting audio from Orpheus for voice '{voice}'...")
        with requests.post(url, headers=headers, data=json.dumps(payload), stream=True, timeout=500) as response:
            response.raise_for_status()
            total_length = int(response.headers.get('content-length', 0))
            bytes_written = 0
            with open(output_path, "wb") as out_file:
                for chunk in response.iter_content(chunk_size=8192):
                    out_file.write(chunk)
                    bytes_written += len(chunk)
                    if progress_callback and total_length > 0:
                        percent = int(100 * bytes_written / total_length)
                        progress_callback(min(percent, 99))
            if progress_callback:
                progress_callback(100)
        log(f"Audio generated and saved to: {output_path}")
        return output_path
    except Exception as e:
        log(f"Error generating speech for voice '{voice}': {e}")
        return None
