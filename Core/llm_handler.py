# ============================================================================
# llm_handler.py - LLM (Large Language Model) Handler for LegalTTSV2
#
# This module provides the get_llm_response function, which sends text and a system
# prompt to an LLM (such as an Ollama or Gemini model) and returns the generated response.
# It supports streaming responses for progress bar updates and can be used with or without
# a model (in which case the document text is returned directly). This module is called
# by the main application workflow to handle all LLM-related operations.
# ============================================================================


import os
import requests
import ollama
from dotenv import load_dotenv

load_dotenv()
OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434')

def log(msg, include_ollama_status=False):
    # Log function for Gradio and CLI: appends messages to a log file for persistent status tracking.
    # Optionally queries Ollama for model status and appends this info to the log.
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs', 'llm_status.log')
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    log_entry = msg
    if include_ollama_status:
        try:
            # Query Ollama's /api/tags endpoint for available models and status
            tags_url = f"{OLLAMA_API_URL.rstrip('/')}/api/tags"
            resp = requests.get(tags_url, timeout=2)
            if resp.ok:
                data = resp.json()
                tags = data.get('models', [])
                tag_names = ', '.join([t.get('name', '') for t in tags])
                log_entry += f" | Ollama models: {tag_names}"
            else:
                log_entry += " | Ollama status: unavailable"
        except Exception as e:
            log_entry += f" | Ollama status error: {e}"
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(log_entry + '\n')

def get_llm_response(model_name, system_prompt, text, progress_callback=None, log_callback=None):
    # Generator for Gradio: yields log/progress updates and streamed LLM response chunks.
    def _log(msg):
        log_msg = f"LLM Logs: {msg}"
        if log_callback:
            log_callback(log_msg)
        else:
            log(log_msg)
        yield log_msg

    if model_name == "no_model":
        yield from _log("No model selected. Using document text directly.")
        if progress_callback:
            progress_callback(100)
        yield text
        return
    if model_name in ["gemini-2.5-pro", "gemini-2.5-flash"]:
        yield from _log("Gemini API model selected. Skipping Ollama call.")
        if progress_callback:
            progress_callback(100)
        yield text
        return

    yield from _log(f"Sending text to Ollama model: {model_name}")
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
                progress_callback(min(i, 99))
            # Yield each chunk as it arrives for Gradio streaming
            yield content
        if progress_callback:
            progress_callback(100)
        yield from _log("AI response received from Ollama.")
    except Exception as e:
        yield from _log(f"Error communicating with Ollama: {e}")
