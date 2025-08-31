# ============================================================================
# prompt_handler.py - Prompt File Loader for LegalTTSV2
#
# This module provides the load_prompt function, which loads and returns the
# contents of a system prompt file for use with LLMs. It is used by the main
# workflow and other modules to retrieve prompt text for AI processing.
# ============================================================================

import os

def load_prompt(prompt_file):
    # Loads and returns the contents of a prompt file for use as a system prompt for LLMs.
    # Returns an empty string if the file does not exist or an error occurs.
    if not prompt_file or not os.path.isfile(prompt_file):
        return ""
    try:
        with open(prompt_file, "r", encoding="utf-8") as pf:
            return pf.read()
    except Exception as e:
        print(f"Error reading prompt file '{prompt_file}': {e}")
        return ""

def resolve_prompt_file(selected_prompt, prompt_options, custom_prompt_path):
    """
    Returns the correct prompt file path based on GUI selection.
    If selected_prompt == '__custom__', returns custom_prompt_path.
    Otherwise, returns prompt_options[selected_prompt].
    """
    if selected_prompt == "__custom__":
        return custom_prompt_path
    return prompt_options.get(selected_prompt, "")
