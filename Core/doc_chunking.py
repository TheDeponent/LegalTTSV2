
# ============================================================================
# doc_chunking.py - Paragraph Chunking Utility for LegalTTSV2
#
# This module provides the split_long_paragraphs function, which splits long
# paragraphs into smaller chunks suitable for LLM and TTS processing. It attempts
# to break at sentence boundaries when possible, and is used by the main workflow
# and other modules to ensure text is processed in manageable pieces. All chunking
# logic for document and AI output is handled here.
# ============================================================================

import re
from Core.constants import MAX_CHUNK_LENGTH

def split_long_paragraphs(paragraphs, max_length=MAX_CHUNK_LENGTH):
    # Splits paragraphs longer than max_length into smaller chunks, breaking at sentence boundaries if possible.
    # Returns a list of text chunks for further processing by LLM or TTS modules.
    chunks = []
    for para in paragraphs:
        if len(para) <= max_length:
            # If the paragraph is short enough, add it as-is
            chunks.append(para)
        else:
            # Otherwise, break the paragraph into smaller chunks
            start = 0
            while start < len(para):
                if len(para) - start <= max_length:
                    # Add the last chunk if it's within the limit
                    chunks.append(para[start:].strip())
                    break
                split_idx = start + max_length
                # Try to break at a sentence boundary (period or exclamation mark)
                match = re.search(r'[.!]', para[split_idx:])
                if match:
                    end = split_idx + match.end()
                    chunks.append(para[start:end].strip())
                    start = end
                else:
                    # If no sentence boundary, break at max_length
                    chunks.append(para[start:start+max_length].strip())
                    start += max_length
    return chunks
