
# ============================================================================
# voice_assignment.py - Voice Assignment Utility for LegalTTSV2
#
# This module provides the assign_voices_to_chunks function, which parses AI output
# or document text for speaker tags and assigns voices to each chunk for TTS processing.
# It uses the split_long_paragraphs function to ensure all chunks are within the TTS
# length limit. This module is called by the main workflow and Gemini handler to
# automate voice assignment for multi-speaker and summary scenarios.
# ============================================================================

import re
from Core.doc_chunking import split_long_paragraphs

def assign_voices_to_chunks(text, user_voice, all_voices, max_length=750):
    # Parses tags, splits long paragraphs, and assigns voices to chunks for TTS processing.
    # Returns a list of (chunk, assigned_voice) tuples for downstream audio generation.
    # split_long_paragraphs is used to ensure all chunks are within the TTS length limit.
    tag_pattern = re.compile(r'(<AI Summary>|<SPEAKER \d+>)', re.IGNORECASE)
    parts = tag_pattern.split(text)
    chunks = []
    i = 0
    while i < len(parts):
        if tag_pattern.match(parts[i]):
            # If a tag is found, combine it with the following text
            if i + 1 < len(parts):
                chunks.append(parts[i] + parts[i+1])
                i += 2
            else:
                chunks.append(parts[i])
                i += 1
        else:
            # If no tag, just add the text chunk
            if parts[i].strip():
                chunks.append(parts[i])
            i += 1
    # Assign voices to each chunk based on tags
    tag_voice_map = {}
    other_voices = [v for v in all_voices if v != user_voice]
    voice_idx = 0
    assigned = []
    for chunk in chunks:
        tag_match = re.match(r'<(AI Summary|SPEAKER \d+)>', chunk.strip(), re.IGNORECASE)
        if tag_match:
            tag = tag_match.group(0).upper()
            if tag in tag_voice_map:
                voice = tag_voice_map[tag]
            else:
                if other_voices:
                    voice = other_voices[voice_idx % len(other_voices)]
                    voice_idx += 1
                else:
                    voice = user_voice
                tag_voice_map[tag] = voice
        else:
            voice = user_voice
        # Remove tags and split long paragraphs inside chunk
        chunk_text = re.sub(r'<(AI Summary|SPEAKER \d+)>', '', chunk, flags=re.IGNORECASE).strip()
        for sub_chunk in split_long_paragraphs([chunk_text], max_length=max_length):
            if sub_chunk:
                assigned.append((sub_chunk, voice))
    return assigned
