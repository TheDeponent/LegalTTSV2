# Voice assignment utility for LegalTTSV2 (Gradio version)
# Provides assign_voices_to_chunks to parse AI output or document text for speaker tags and assign voices for TTS.
# Uses split_long_paragraphs to ensure all chunks are within the TTS length limit. All logic is GUI-agnostic.

import re
from Core.doc_utils import split_long_paragraphs
from Core.llm_handler import log

def assign_voices_to_chunks(text, user_voice, all_voices, max_length=750):
    # Parse tags, split long paragraphs, and assign voices to chunks for TTS processing.
    # Returns a list of (chunk, assigned_voice) tuples for downstream audio generation.
    tag_pattern = re.compile(r'(<(?:AI Summary|SPEAKER[ _]\d+)>)', re.IGNORECASE)
    parts = tag_pattern.split(text)
    chunks = []
    i = 0
    while i < len(parts):
        # A non-tag part is always at an even index
        if parts[i].strip():
            # Check if there is a corresponding tag part
            if i + 1 < len(parts):
                # Combine the tag with the text that follows it
                chunks.append(parts[i+1] + parts[i])
                i += 2
            else:
                chunks.append(parts[i])
                i += 1
        else:
            i += 1

    # If the text starts with a tag, the first part will be empty. The logic needs to handle this.
    # Let's refine the chunking logic to be more robust.
    chunks = []
    # Find all tags and their positions
    tags_with_indices = [(m.group(0), m.start()) for m in tag_pattern.finditer(text)]
    last_idx = 0
    for tag, start_idx in tags_with_indices:
        # Add the text before the tag
        if start_idx > last_idx:
            chunks.append(text[last_idx:start_idx])
        # The "chunk" is the tag itself, which we'll use for voice assignment later
        chunks.append(tag)
        last_idx = start_idx + len(tag)
    # Add any remaining text after the last tag
    if last_idx < len(text):
        chunks.append(text[last_idx:])

    # Now, let's process these chunks to assign voices
    assigned = []
    tag_voice_map = {}
    female_voices = [v for v in all_voices if v in {"Tara", "Leah", "Jess", "Mia", "Zoe"} and v != user_voice]
    male_voices = [v for v in all_voices if v in {"Leo", "Dan", "Zac"} and v != user_voice]
    female_idx, male_idx = 0, 0
    next_is_female = True
    
    current_voice = user_voice

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        tag_match = tag_pattern.match(chunk)
        if tag_match:
            tag = tag_match.group(0).upper().replace('_', ' ') # Normalize tag
            if tag in tag_voice_map:
                current_voice = tag_voice_map[tag]
            else:
                if female_voices or male_voices:
                    if next_is_female and female_voices:
                        new_voice = female_voices[female_idx % len(female_voices)]
                        female_idx += 1
                        next_is_female = False
                    elif male_voices:
                        new_voice = male_voices[male_idx % len(male_voices)]
                        male_idx += 1
                        next_is_female = True
                    else:
                        new_voice = (female_voices + male_voices)[0]
                    
                    log(f"Assigned voice '{new_voice}' to tag {tag}")
                    tag_voice_map[tag] = new_voice
                    current_voice = new_voice
                else:
                    # No alternate voices available, use user_voice
                    tag_voice_map[tag] = user_voice
                    current_voice = user_voice
            # This chunk is just a tag, so we continue to the next chunk which contains the text
            continue
        
        # This chunk is text, assign the current_voice
        for sub_chunk in split_long_paragraphs([chunk], max_length=max_length):
            if sub_chunk:
                assigned.append((sub_chunk, current_voice))

    # If no tags were found at all, the whole text gets the user_voice
    if not tags_with_indices:
        for sub_chunk in split_long_paragraphs([text], max_length=max_length):
            if sub_chunk:
                assigned.append((sub_chunk, user_voice))
                
    log(f"Total assigned chunks: {len(assigned)}")
    return assigned
