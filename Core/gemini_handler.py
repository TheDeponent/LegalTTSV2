# ============================================================================
# gemini_handler.py - Gemini API Handler for LegalTTSV2 (Gradio Edition)
#
# Provides backend functions for interacting with the Gemini LLM API, including file upload,
# response handling, and voice assignment. No GUI or user interaction code; designed for use
# in the Gradio pipeline.
# ============================================================================

import os
import requests
import google.generativeai as genai
import pythoncom
import tempfile
from docx2pdf import convert as docx2pdf_convert
from dotenv import load_dotenv
from Core.voice_assignment import assign_voices_to_chunks
from Core.constants import MAX_CHUNK_LENGTH

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def process_gemini_file_workflow(docx_path, model_name, system_prompt, voice_name, all_voices, max_length=MAX_CHUNK_LENGTH):
    # Uploads a PDF to Gemini, gets the full LLM response, and chunks for TTS/Orpheus after.
    # Returns (chunks_and_voices, llm_response) tuple for further processing.
    debug_logs = []
    if not GOOGLE_API_KEY:
        debug_logs.append("GOOGLE_API_KEY not set in environment.")
        return None, None, debug_logs
    genai.configure(api_key=GOOGLE_API_KEY)
    ext = os.path.splitext(docx_path)[1].lower()
    pdf_path = docx_path
    if ext == ".docx":
        temp_dir = tempfile.gettempdir()
        base = os.path.splitext(os.path.basename(docx_path))[0]
        pdf_path = os.path.join(temp_dir, f"{base}_gemini_upload.pdf")
        try:
            pythoncom.CoInitialize()
            docx2pdf_convert(docx_path, pdf_path)
            debug_logs.append(f"Converted DOCX to PDF for Gemini upload: {pdf_path}")
        except Exception as e:
            debug_logs.append(f"Failed to convert DOCX to PDF for Gemini upload: {e}")
            return None, None, debug_logs
    elif ext != ".pdf":
        debug_logs.append(f"Unsupported file type for Gemini file upload: {ext}")
        return None, None, debug_logs
    try:
        debug_logs.append(f"Uploading file to Gemini: {pdf_path}")
        uploaded_file = genai.upload_file(path=pdf_path, mime_type="application/pdf")
        debug_logs.append(f"Uploaded file URI: {uploaded_file.uri}")
        model = genai.GenerativeModel(model_name)
        debug_logs.append(f"Calling Gemini model: {model_name}")
        response = model.generate_content([
            {"text": system_prompt},
            {"file_data": {"file_uri": uploaded_file.uri}}
        ])
        # Log a summary of the Gemini response structure for debugging, but avoid serializing non-serializable objects
        try:
            response_json = response._result if hasattr(response, '_result') else None
            if response_json:
                debug_logs.append(f"Gemini response _result type: {type(response_json)}")
            else:
                debug_logs.append(f"Gemini response type: {type(response)}")
        except Exception as e:
            debug_logs.append(f"Could not inspect Gemini response object: {e}")
        # Try to extract only the actual text content from the Gemini response
        llm_response = None
        try:
            # Try to extract from candidates if present
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                content = getattr(candidate, 'content', None)
                parts = getattr(content, 'parts', None) if content else None
                if parts and isinstance(parts, list):
                    # Only include non-empty, non-metadata text parts
                    text_parts = []
                    for p in parts:
                        if isinstance(p, dict) and "text" in p:
                            text = str(p.get("text", "")).strip()
                        elif isinstance(p, str):
                            text = p.strip()
                        else:
                            text = str(p).strip()
                        if text and not text.lower().startswith("response:") and not text.lower().startswith("generatecontentresponse("):
                            text_parts.append(text)
                    llm_response = "\n".join(text_parts)
            if not llm_response:
                # Fallback: try .text or str(response), but filter out metadata
                raw = getattr(response, 'text', None) or str(response)
                if raw and not raw.lower().startswith("response:") and not raw.lower().startswith("generatecontentresponse("):
                    llm_response = raw
        except Exception as e:
            debug_logs.append(f"Error extracting LLM response from Gemini: {e}")
            llm_response = ""
        debug_logs.append(f"Gemini LLM response (extracted): {llm_response[:1000]}")
        if not llm_response or not llm_response.strip():
            debug_logs.append("Gemini LLM response was empty.")
            return None, None, debug_logs
        # Only chunk the LLM response for TTS/Orpheus after getting the full response
        chunks_and_voices = assign_voices_to_chunks(llm_response, voice_name, all_voices, max_length=max_length)
        # Filter out any chunk that looks like API metadata or is not valid speech text
        def is_valid_chunk(chunk):
            c = chunk.strip()
            return c and not c.lower().startswith("response:") and not c.lower().startswith("generatecontentresponse(")
        filtered_chunks = [(chunk, voice) for (chunk, voice) in (chunks_and_voices or []) if is_valid_chunk(chunk)]
        debug_logs.append(f"Chunking result: {len(filtered_chunks)} valid chunks.")
        if filtered_chunks:
            for idx, (chunk, voice) in enumerate(filtered_chunks[:5]):
                debug_logs.append(f"Chunk {idx+1}: {repr(chunk)[:200]} | Voice: {voice}")
        if not filtered_chunks:
            debug_logs.append("Gemini LLM response could not be chunked for TTS.")
            return None, llm_response, debug_logs
        return filtered_chunks, llm_response, debug_logs
    except Exception as e:
        debug_logs.append(f"Gemini file upload or content generation failed: {e}")
        return None, None, debug_logs

def get_gemini_response(text, model_name, system_prompt, api_key):
    # Sends a text prompt to the Gemini API and returns the generated response text.
    # Accepts an optional log_callback for logging to Gradio UI.
    def log(msg):
        if hasattr(get_gemini_response, 'log_callback') and get_gemini_response.log_callback:
            get_gemini_response.log_callback(msg)
        elif hasattr(get_gemini_response, '_log_callback') and get_gemini_response._log_callback:
            get_gemini_response._log_callback(msg)
        else:
            pass  # No-op if no callback set

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"role": "user", "parts": [{"text": text}]}]
    }
    if system_prompt:
        data["system_instruction"] = {"role": "system", "parts": [{"text": system_prompt}]}
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=120)
        log(f"Gemini API raw response: {resp.status_code} {resp.text}")
        resp.raise_for_status()
        result = resp.json()
        candidates = result.get("candidates")
        if candidates and "content" in candidates[0] and "parts" in candidates[0]["content"]:
            return candidates[0]["content"]["parts"][0].get("text", "")
        log(f"Gemini API unexpected response structure: {result}")
        return None
    except Exception as e:
        log(f"Gemini API error: {e}\nFull response: {getattr(e, 'response', None)}")
        return None

