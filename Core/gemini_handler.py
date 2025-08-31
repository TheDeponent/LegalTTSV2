# ============================================================================
# gemini_handler.py - Gemini API Handler for LegalTTSV2
# This module provides functions for interacting with the Gemini LLM API, including
# file upload, chunked text processing, and response handling. It is used by the main
# application workflow to process documents with Gemini models, assign voices, and
# save AI responses. All Gemini API logic is handled here.
# ============================================================================

import os
import requests
import google.generativeai as genai
import re
from dotenv import load_dotenv
from Core.constants import MAX_CHUNK_LENGTH

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def process_gemini_file_workflow(docx_path, model_name, system_prompt, voice_name, all_voices, max_length=MAX_CHUNK_LENGTH):
    # Always upload the file (PDF or DOCX converted to PDF) to Gemini, get the full response, and only chunk the response for TTS/Orpheus after.
    # Returns (chunks_and_voices, llm_response) tuple for further processing.
    if not GOOGLE_API_KEY:
        print("GOOGLE_API_KEY not set in environment.")
        return None, None
    genai.configure(api_key=GOOGLE_API_KEY)
    ext = os.path.splitext(docx_path)[1].lower()
    pdf_path = docx_path
    if ext == ".docx":
        import tempfile
        from docx2pdf import convert as docx2pdf_convert
        temp_dir = tempfile.gettempdir()
        base = os.path.splitext(os.path.basename(docx_path))[0]
        pdf_path = os.path.join(temp_dir, f"{base}_gemini_upload.pdf")
        try:
            docx2pdf_convert(docx_path, pdf_path)
        except Exception as e:
            print(f"Failed to convert DOCX to PDF for Gemini upload: {e}")
            return None, None
    elif ext != ".pdf":
        print(f"Unsupported file type for Gemini file upload: {ext}")
        return None, None
    try:
        uploaded_file = genai.upload_file(path=pdf_path, mime_type="application/pdf")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content([
            {"text": system_prompt},
            {"file_data": {"file_uri": uploaded_file.uri}}
        ])
        llm_response = response.text if hasattr(response, 'text') else str(response)
        # Only chunk the LLM response for TTS/Orpheus after getting the full response
        from Core.voice_assignment import assign_voices_to_chunks
        chunks_and_voices = assign_voices_to_chunks(llm_response, voice_name, all_voices, max_length=max_length)
        return chunks_and_voices, llm_response
    except Exception as e:
        print(f"Gemini file upload or content generation failed: {e}")
        return None, None

def get_gemini_response(text, model_name, system_prompt, api_key):
    # Sends a text prompt to the Gemini API and returns the generated response text.
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"role": "user", "parts": [{"text": text}]}]
    }
    if system_prompt:
        data["system_instruction"] = {"role": "system", "parts": [{"text": system_prompt}]}
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=120)
        print(f"Gemini API raw response: {resp.status_code} {resp.text}")
        resp.raise_for_status()
        result = resp.json()
        candidates = result.get("candidates")
        if candidates and "content" in candidates[0] and "parts" in candidates[0]["content"]:
            return candidates[0]["content"]["parts"][0].get("text", "")
        print(f"Gemini API unexpected response structure: {result}")
        return None
    except Exception as e:
        print(f"Gemini API error: {e}\nFull response: {getattr(e, 'response', None)}")
        return None

def process_gemini_chunked_workflow(docx_path, model_name, system_prompt, extract_text_func, get_gemini_response_func, assign_voices_func, voice_name, all_voices, text_outputs_dir, output_base, chunk_size=25000, max_length=750):
    """
    Deprecated: For Gemini API, always use file upload. This function is kept for backward compatibility but will call process_gemini_file_workflow.
    """
    print("[Info] For Gemini API, always uploading file and chunking after response.")
    return process_gemini_file_workflow(docx_path, model_name, system_prompt, voice_name, all_voices, max_length=max_length)

def gemini_chunked_response(docx_path, model_name, system_prompt, extract_text_func, get_gemini_response_func, chunk_size=25000):
    # Extracts text from docx_path, splits into chunk_size, calls Gemini API for each chunk, and returns the joined response.
    # extract_text_func is used to extract text from docx_path; get_gemini_response_func is used to call Gemini API for a chunk.
    full_text = extract_text_func(docx_path)
    chunks = []
    start = 0
    while start < len(full_text):
        if len(full_text) - start <= chunk_size:
            chunks.append(full_text[start:].strip())
            break
        split_idx = start + chunk_size
        # Try to break at a sentence boundary (period or exclamation mark)
        match = re.search(r'[.!]', full_text[split_idx:])
        if match:
            end = split_idx + match.end()
            chunks.append(full_text[start:end].strip())
            start = end
        else:
            chunks.append(full_text[start:start+chunk_size].strip())
            start += chunk_size
    print(f"Split document into {len(chunks)} chunk(s) for Gemini API.")
    all_responses = []
    for idx, chunk_text in enumerate(chunks):
        print(f"Sending chunk {idx+1}/{len(chunks)} to Gemini API...")
        resp = get_gemini_response_func(chunk_text, model_name, system_prompt)
        if not resp:
            print(f"Failed to get response from Gemini API for chunk {idx+1}.")
            return None
        all_responses.append(resp)
    return '\n'.join(all_responses)
import google.generativeai as genai

def configure_gemini(api_key):
    # Configures the Gemini API client with the provided API key.
    genai.configure(api_key=api_key)


def upload_pdf_and_generate_summary(pdf_path, prompt, model_name):
    # Uploads a PDF to Gemini Files API and generates a summary using the given prompt and model.
    # Returns the response text for further processing.
    uploaded_file = genai.upload_file(path=pdf_path, mime_type="application/pdf")
    model = genai.GenerativeModel(model_name)
    response = model.generate_content([
        {"text": prompt},
        {"file_data": {"file_uri": uploaded_file.uri}}
    ])
    return response.text
