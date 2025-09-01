# Audio utilities for LegalTTSV2 (Gradio version)
# Provides functions to concatenate audio files and clean up intermediates.
# All logic is GUI-agnostic and suitable for use with a Gradio web interface.

import os
from pydub import AudioSegment

def concatenate_audio(audio_paths, output_dir, pause_ms=1000, source_doc_path=None):
    # Concatenate a list of WAV file paths with a pause between each segment.
    # Returns the path to the combined audio file for further processing.
    if not audio_paths:
        return None
    try:
        pause = AudioSegment.silent(duration=pause_ms)
        combined = AudioSegment.from_wav(audio_paths[0])
        if len(combined) < 500:  # less than 0.5s
            # Warn if the first file is too short
            print(f"Warning: First audio file '{audio_paths[0]}' is very short ({len(combined)/1000:.2f}s)")
        for path in audio_paths[1:]:
            seg = AudioSegment.from_wav(path)
            if len(seg) < 500:
                print(f"Warning: Audio file '{path}' is very short ({len(seg)/1000:.2f}s)")
            combined += pause + seg
        os.makedirs(output_dir, exist_ok=True)
        # Use the base name of the original document if available, otherwise use a default name
        if source_doc_path:
            orig_base = os.path.splitext(os.path.basename(source_doc_path))[0]
        else:
            orig_base = 'combined_audio'
        combined_path = os.path.join(output_dir, f"{orig_base}.wav")
        combined.export(combined_path, format='wav')
        return combined_path
    except Exception as e:
        print(f"Error during audio concatenation: {str(e)}")
        return None

def concatenate_and_cleanup_audio(audio_paths, output_dir, source_doc_path=None, pause_ms=1000):
    # Concatenate audio files and remove intermediate files. Returns the path to the combined audio file.
    combined_path = concatenate_audio(audio_paths, output_dir, pause_ms=pause_ms, source_doc_path=source_doc_path)
    # Remove intermediate audio files (do not delete the combined output)
    for temp_audio in audio_paths:
        try:
            if os.path.exists(temp_audio) and temp_audio != combined_path:
                os.remove(temp_audio)
        except Exception as e:
            print(f"Warning: Could not remove temp audio file '{temp_audio}': {str(e)}")
    return combined_path


