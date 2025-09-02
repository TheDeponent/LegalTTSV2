# Voice assignment utility for LegalTTSV2 (Gradio version)
# Provides assign_voices_to_chunks to parse AI output or document text for speaker tags and assign voices for TTS.
# Uses split_long_paragraphs to ensure all chunks are within the TTS length limit. All logic is GUI-agnostic.

import re
from Core.doc_utils import split_long_paragraphs
from Core.llm_handler import log

def assign_voices_to_chunks(text, user_voice, all_voices, max_length=750):
    # Parse tags, split long paragraphs, and assign voices to chunks for TTS processing.
    # Returns a list of (chunk, assigned_voice) tuples for downstream audio generation.
    tag_pattern = re.compile(r'(<AI Summary>|<SPEAKER \d+>)', re.IGNORECASE)
    parts = tag_pattern.split(text)
    chunks = []
    i = 0
    while i < len(parts):
        if tag_pattern.match(parts[i]):
            if i + 1 < len(parts):
                chunks.append(parts[i] + parts[i+1])
                i += 2
            else:
                chunks.append(parts[i])
                i += 1
        else:
            if parts[i].strip():
                chunks.append(parts[i])
            i += 1
    tag_voice_map = {}
    # Gender mapping for voices
    female_voices = [v for v in all_voices if v in {"Tara", "Leah", "Jess", "Mia", "Zoe"} and v != user_voice]
    male_voices = [v for v in all_voices if v in {"Leo", "Dan", "Zac"} and v != user_voice]
    # Alternate between female and male voices
    female_idx = 0
    male_idx = 0
    next_is_female = True
    assigned = []
    voice_tag_pattern = re.compile(r'voice:([a-zA-Z0-9_\-]+)', re.IGNORECASE)
    for chunk in chunks:
        tag_match = re.match(r'<(AI Summary|SPEAKER \d+)>', chunk.strip(), re.IGNORECASE)
        # Check for explicit voice:NAME tag in the chunk text
        voice_tag_match = voice_tag_pattern.search(chunk)
        if voice_tag_match:
            explicit_voice = voice_tag_match.group(1).capitalize()
            if explicit_voice in all_voices:
                voice = explicit_voice
                log(f"Explicit voice tag found: {explicit_voice}")
            else:
                voice = user_voice
            chunk_text = voice_tag_pattern.sub('', chunk)
        elif tag_match:
            tag = tag_match.group(0).upper()
            if tag in tag_voice_map:
                voice = tag_voice_map[tag]
            else:
                # Alternate between female and male voices
                if female_voices or male_voices:
                    if next_is_female and female_voices:
                        voice = female_voices[female_idx % len(female_voices)]
                        female_idx += 1
                        next_is_female = False
                    elif male_voices:
                        voice = male_voices[male_idx % len(male_voices)]
                        male_idx += 1
                        next_is_female = True
                    else:
                        # Fallback if one gender list is empty
                        voice = (female_voices + male_voices)[0]
                    log(f"Assigned voice '{voice}' to tag {tag}")
                else:
                    voice = user_voice
                tag_voice_map[tag] = voice
            chunk_text = re.sub(r'<(AI Summary|SPEAKER \d+)>', '', chunk, flags=re.IGNORECASE)
        else:
            voice = user_voice
            chunk_text = chunk
        chunk_text = re.sub(r'<(AI Summary|SPEAKER \d+)>', '', chunk_text, flags=re.IGNORECASE).strip()
        for sub_chunk in split_long_paragraphs([chunk_text], max_length=max_length):
            if sub_chunk:
                assigned.append((sub_chunk, voice))
    log(f"Total assigned chunks: {len(assigned)}")
    return assigned
