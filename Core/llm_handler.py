
# ============================================================================
# llm_handler.py - LLM (Large Language Model) Handler for LegalTTSV2
#
# This module provides the get_llm_response function, which sends text and a system
# prompt to an LLM (such as an Ollama or Gemini model) and returns the generated response.
# It supports streaming responses for progress bar updates and can be used with or without
# a model (in which case the document text is returned directly). This module is called
# by the main application workflow to handle all LLM-related operations.
# ============================================================================

import ollama

def get_llm_response(model_name, system_prompt, text, progress_callback=None):
    # Returns the LLM response for the given text and system prompt using the selected model.
    # If no model is selected, returns the document text directly.
    # If a Gemini API model is selected, returns the text (already processed by Gemini_handler).
    # Otherwise, sends the request to the Ollama model and streams the response for progress updates.
    if model_name == "no_model":
        # No model selected; return the document text directly
        print("No model selected. Using document text directly.")
        if progress_callback:
            progress_callback(100)  # Instantly complete progress
        return text
    if model_name in ["gemini-2.5-pro", "gemini-2.5-flash"]:
        # Gemini_handler is used to process the text for Gemini API models; skip Ollama call
        print(f"Gemini API model selected. Skipping Ollama call.")
        if progress_callback:
            progress_callback(100)
        return text

    # Ollama is used to generate a response from the selected LLM model
    print(f"Sending text to Ollama model: {model_name}")
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': text}
    ]
    try:
        stream = ollama.chat(model=model_name, messages=messages, stream=True)
        llm_response = ""
        i = 0
        for chunk in stream:
            content = chunk['message']['content']
            llm_response += content
            i += 1
            if progress_callback:
                # Update the progress bar for each chunk received
                progress_callback(min(i, 99))

        if progress_callback:
            progress_callback(100)  # Signal completion

        print("AI Response:\n", llm_response)
        return llm_response
    except Exception as e:
        print(f"Error communicating with Ollama: {e}")
        return None
