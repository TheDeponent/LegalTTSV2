# ============================================================================
# audio_utils.py - Audio Concatenation Utility for LegalTTSV2
#
# This module provides functions to combine multiple audio files (WAV) into a single output file
# with optional pauses between them, and to clean up intermediate files. It is used by the main
# application workflow to produce a single audio output from multiple TTS-generated chunks.
# All audio concatenation and cleanup logic is handled here.
# ============================================================================

import os
from pydub import AudioSegment

def concatenate_audio(audio_paths, output_dir, pause_ms=1000, source_doc_path=None):
    # Concatenates a list of audio file paths with a pause between each segment.
    # Returns the path to the combined audio file for playback or further processing.
    # pydub.AudioSegment is used to load and concatenate audio files.
    if not audio_paths:
        return None
    pause = AudioSegment.silent(duration=pause_ms)
    combined = AudioSegment.from_wav(audio_paths[0])
    for path in audio_paths[1:]:
        seg = AudioSegment.from_wav(path)
        combined += pause + seg
    # os.makedirs is used to ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    # Use the base name of the original document if available, otherwise use a default
    if source_doc_path:
        orig_base = os.path.splitext(os.path.basename(source_doc_path))[0]
    elif hasattr(concatenate_audio, 'source_doc_path') and concatenate_audio.source_doc_path:
        orig_base = os.path.splitext(os.path.basename(concatenate_audio.source_doc_path))[0]
    else:
        orig_base = 'combined_audio'
    combined_path = os.path.join(output_dir, f"{orig_base}.wav")
    combined.export(combined_path, format='wav')
    return combined_path

def concatenate_and_cleanup_audio(audio_paths, output_dir, source_doc_path=None, pause_ms=1000):
    # Concatenates audio files and cleans up intermediate files. Returns the path to the combined audio file.
    # This function is intended to be called by the main app, replacing any manual cleanup logic.
    combined_path = concatenate_audio(audio_paths, output_dir, pause_ms=pause_ms, source_doc_path=source_doc_path)
    # Clean up intermediate audio files (do not delete the combined output)
    for temp_audio in audio_paths:
        try:
            if os.path.exists(temp_audio) and temp_audio != combined_path:
                os.remove(temp_audio)
                print(f"Deleted intermediate audio file: {temp_audio}")
        except Exception as e:
            print(f"Failed to delete {temp_audio}: {e}")
    return combined_path

def play_audio(audio_path):
    # Plays the audio file using the system's default player for the current OS.
    import sys
    import subprocess
    import time
    if not audio_path or not os.path.exists(audio_path):
        return
    try:
        if sys.platform == "win32":
            os.startfile(audio_path)
        elif sys.platform == "darwin":
            subprocess.run(["open", audio_path])
        else:
            subprocess.run(["xdg-open", audio_path])
        # Optionally, wait for the audio to finish (if needed)
        # time.sleep(AudioSegment.from_wav(audio_path).duration_seconds)
    except Exception as e:
        print(f"Error playing audio: {e}")

def play_and_report_combined_audio(combined_path):
    # Loads the combined audio, prints its duration, and plays it for the user.
    from pydub import AudioSegment
    if combined_path and os.path.exists(combined_path):
        combined = AudioSegment.from_wav(combined_path)
        print(f"Combined audio duration: {combined.duration_seconds:.2f} seconds, file: {combined_path}")
        play_audio(combined_path)