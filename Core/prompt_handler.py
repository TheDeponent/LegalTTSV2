
# prompt_handler.py - Prompt Loader for LegalTTSV2 (Gradio Edition)
#
# Provides functions to load prompt text for LLMs, supporting both file-based and custom (string) prompts.
# Used by the Gradio pipeline to retrieve the system prompt for AI processing.
import os

# Returns (system_prompt, status_message)
def get_system_prompt(system_prompt_key, prompt_options, custom_prompt_path):
    """
    Resolves and loads the system prompt for LLMs.
    - If system_prompt_key == '__custom__', uses custom_prompt_path as a file if it exists, else as a string.
    - Otherwise, loads the prompt from the resolved file in prompt_options.
    Returns (system_prompt, status_message)
    """
    import logging
    logger = logging.getLogger("PromptHandler")
    def log(msg):
        logger.info(msg)

    # Determine the prompt file path if not custom
    if system_prompt_key == "__custom__":
        # Always treat custom_prompt_path as the prompt text, not a file path
        system_prompt = custom_prompt_path or ""
        status = "Using custom prompt text from UI."
        log(status)
        return system_prompt, status
    else:
        prompt_file = prompt_options.get(system_prompt_key, "")
        if not prompt_file or not os.path.isfile(prompt_file):
            log(f"Prompt file not found: {prompt_file}")
            return "", f"Failed to load system prompt: {prompt_file}"
        try:
            with open(prompt_file, "r", encoding="utf-8") as pf:
                system_prompt = pf.read()
            status = f"Loaded prompt: {prompt_file}"
            log(status)
            return system_prompt, status
        except Exception as e:
            log(f"Error reading prompt file '{prompt_file}': {e}")
            return "", f"Failed to load system prompt: {prompt_file}"
