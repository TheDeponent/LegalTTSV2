# This module provides STT-based deduplication for audio files.
# Usage: import and call clean_audio_with_stt(input_path, output_path, whisper_model="base.en")

import os
from faster_whisper import WhisperModel
from pydub import AudioSegment

def log_word_timestamps(input_path, all_words):
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(input_path))[0]
    log_path = os.path.join(logs_dir, f"{base}_WHISPERLOG.txt")
    with open(log_path, 'w', encoding='utf-8') as f:
        for w in all_words:
            f.write(f"{w['word']}\t{w['start']:.2f}\t{w['end']:.2f}\n")
    print(f"Whisper word log saved to: {log_path}")

def auto_cleaned_filename(input_path):
    base, ext = os.path.splitext(input_path)
    return f"{base}_Cleaned{ext}"

def find_adjacent_repeats(words, min_words=1, max_phrase_len=20, max_gap_ms=2000):
    segments_to_remove = []
    i = 0
    n = len(words)
    while i < n:
        found_repeat = False
        for phrase_len in range(max_phrase_len, min_words - 1, -1):
            if i + 2 * phrase_len > n:
                continue
            seq1 = [w['word'].lower().strip() for w in words[i:i+phrase_len]]
            seq2 = [w['word'].lower().strip() for w in words[i+phrase_len:i+2*phrase_len]]
            if seq1 == seq2:
                gap = (words[i+phrase_len]['start'] - words[i+phrase_len-1]['end']) * 1000
                if gap <= max_gap_ms:
                    start_time_ms = words[i+phrase_len]['start'] * 1000
                    end_time_ms = words[i+2*phrase_len-1]['end'] * 1000
                    segments_to_remove.append((start_time_ms, end_time_ms))
                    print(f"Found repeat: {' '.join(seq1)} (len={phrase_len}) at {start_time_ms/1000:.2f}s")
                    i += phrase_len
                    found_repeat = True
                    break
        # Special case: single word repeated 3+ times in a row
        if not found_repeat and i+2 < n:
            w1 = words[i]['word'].lower().strip()
            w2 = words[i+1]['word'].lower().strip()
            w3 = words[i+2]['word'].lower().strip()
            if w1 == w2 == w3:
                repeat_len = 3
                while i+repeat_len < n and words[i+repeat_len]['word'].lower().strip() == w1:
                    repeat_len += 1
                start_time_ms = words[i+1]['start'] * 1000
                end_time_ms = words[i+repeat_len-1]['end'] * 1000
                segments_to_remove.append((start_time_ms, end_time_ms))
                print(f"Found single-word repeat: {w1} x{repeat_len} at {start_time_ms/1000:.2f}s")
                i += repeat_len
                found_repeat = True
        if not found_repeat:
            i += 1
    return segments_to_remove

def clean_audio_with_stt(input_path, output_path, whisper_model="base.en"):
    print("Loading Whisper model...")
    model = WhisperModel(whisper_model, device="cpu", compute_type="int8")
    print(f"Transcribing {input_path} with word-level timestamps...")
    segments, _ = model.transcribe(input_path, word_timestamps=True)
    all_words = []
    for segment in segments:
        for word in segment.words:
            all_words.append({'word': word.word, 'start': word.start, 'end': word.end})
    log_word_timestamps(input_path, all_words)
    to_remove = find_adjacent_repeats(all_words, min_words=1, max_phrase_len=20, max_gap_ms=2000)
    if not to_remove:
        print("No repeated segments found. The audio is already clean.")
        return
    print(f"Found {len(to_remove)} segments to remove. Splicing audio...")
    original_audio = AudioSegment.from_file(input_path)
    to_remove.sort()
    last_cut_end = 0
    clean_audio = AudioSegment.empty()
    for start_ms, end_ms in to_remove:
        clean_audio += original_audio[last_cut_end:start_ms]
        last_cut_end = end_ms
    clean_audio += original_audio[last_cut_end:]
    print(f"Exporting cleaned audio to {output_path}")
    clean_audio.export(output_path, format=output_path.split('.')[-1])
    print("Done!")
