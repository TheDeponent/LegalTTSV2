# ============================================================================
# tts_handler.py - Text-to-Speech (TTS) Handler for LegalTTSV2
#
# This module provides functions for generating speech audio from text using the
# Orpheus TTS API. It is called by the main application workflow to handle all
# TTS-related operations.
# ============================================================================

import os
import requests
import json
import uuid
from dotenv import load_dotenv

load_dotenv()
TTS_ENDPOINT = os.getenv("TTS_ENDPOINT", "http://localhost:5005/v1/audio/speech")

def generate_speech(text, voice="tara"):
    # Generates speech from text using the Orpheus TTS API and saves the result as a WAV file.
    url = TTS_ENDPOINT
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "input": text,
        "model": "orpheus-tts",
        "voice": voice.lower(),
        "response_format": "wav",
        "speed": 1
    }
    try:
        # os and uuid are used to generate a unique output path for the audio file
        outputs_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs"))
        os.makedirs(outputs_dir, exist_ok=True)
        filename = f"tts_{uuid.uuid4().hex}.wav"
        output_path = os.path.join(outputs_dir, filename)

        print("Requesting audio from Orpheus...")
        # requests is used to send the TTS request to the Orpheus API
        with requests.post(url, headers=headers, data=json.dumps(payload), stream=True, timeout=500) as response:
            response.raise_for_status()
            with open(output_path, "wb") as out_file:
                for chunk in response.iter_content(chunk_size=8192):
                    out_file.write(chunk)

        return output_path
    except requests.exceptions.RequestException as e:
        print(f"Error generating speech: {e}")
        return None
