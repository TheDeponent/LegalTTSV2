
# prompt_handler.py - Prompt Loader for LegalTTSV2 (Gradio Edition)
#
# Provides functions to load prompt text for LLMs, supporting both file-based and custom (string) prompts.
# Used by the Gradio pipeline to retrieve the system prompt for AI processing.
import os

# Returns (system_prompt, status_message)
def get_system_prompt(system_prompt_key, prompt_options, prompt_text):
    # Processes the system prompt for LLMs.
    # Uses the prompt_text directly from the UI, which contains either:
    # a) The user's custom prompt (if system_prompt_key == '__custom__')
    # b) The possibly modified template prompt (if system_prompt_key is a template name)
    # Returns (system_prompt, status_message)
    import logging
    logger = logging.getLogger("PromptHandler")
    def log(msg):
        logger.info(msg)

    # Always use the prompt text from the UI
    system_prompt = prompt_text.strip() if prompt_text else ""

    # Replace {ConstantName} tags with values from USER_CONSTANTS
    try:
        from Core.constants import USER_CONSTANTS
        import re
        def replace_tag(match):
            key = match.group(1)
            return str(USER_CONSTANTS.get(key, match.group(0)))
        system_prompt = re.sub(r"{([A-Za-z0-9_]+)}", replace_tag, system_prompt)
    except Exception as e:
        log(f"Prompt constant replacement error: {e}")

    if not system_prompt:
        status = "No prompt text provided."
        log(status)
        return "", status

    if system_prompt_key == "__custom__":
        status = "Using custom prompt from UI."
    else:
        status = f"Using prompt template: {system_prompt_key}"

    log(status)
    return system_prompt, status
