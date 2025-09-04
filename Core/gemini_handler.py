# ============================================================================
# gemini_handler.py - Gemini API Handler for LegalTTSV2
#
# Provides a unified backend function for interacting with the Gemini LLM API,
# handling both file and text inputs.
# ============================================================================

import os
import google.generativeai as genai
import pythoncom
import tempfile
from docx2pdf import convert as docx2pdf_convert
from dotenv import load_dotenv
from Core.voice_assignment import assign_voices_to_chunks
from Core.constants import MAX_CHUNK_LENGTH

# Load environment variables once
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def process_gemini_request(input_path, input_text, model_name, system_prompt, voice_name, all_voices, max_length=MAX_CHUNK_LENGTH):
    """
    Unified function to handle both file and text requests to the Gemini API.
    Yields log messages and returns the final processed audio chunks.
    """
    if not GOOGLE_API_KEY:
        yield "Gemini API key not set in environment. Aborting."
        return [], None
    
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(model_name=model_name, system_instruction=system_prompt)

    prompt_parts = []
    pdf_path = None
    temp_dir = None

    try:
        # --- 1. Prepare Input (File or Text) ---
        if input_path:
            ext = os.path.splitext(input_path)[1].lower()
            if ext == ".docx":
                yield "Converting DOCX to PDF for Gemini upload..."
                temp_dir = tempfile.gettempdir()
                base = os.path.splitext(os.path.basename(input_path))[0]
                pdf_path = os.path.join(temp_dir, f"{base}_gemini_upload.pdf")
                pythoncom.CoInitialize()
                docx2pdf_convert(input_path, pdf_path)
            elif ext == ".pdf":
                pdf_path = input_path
            else:
                yield f"Unsupported file type for Gemini upload: {ext}. Aborting."
                return [], None
            
            yield "Uploading file to Gemini..."
            uploaded_file = genai.upload_file(path=pdf_path)
            prompt_parts.append(uploaded_file)

        elif input_text:
            prompt_parts.append(input_text)
        
        else:
            yield "No input provided (either file or text). Aborting."
            return [], None

        # --- 2. Generate Content from Gemini ---
        yield "Sending request to Gemini model..."
        response = model.generate_content(prompt_parts)
        
        # --- 3. Parse Response and Process for TTS ---
        llm_response = response.text.strip()

        if not llm_response:
            yield "Gemini LLM response was empty."
            return [], None
        
        yield "Gemini response received. Chunking for TTS..."
        chunks_and_voices = assign_voices_to_chunks(llm_response, voice_name, all_voices, max_length=max_length)
        
        if not chunks_and_voices:
            yield "Gemini LLM response could not be chunked for TTS."
            return [], llm_response
            
        yield "Processing complete."
        yield chunks_and_voices, llm_response

    except Exception as e:
        error_message = f"An error occurred in the Gemini workflow: {e}"
        yield error_message
        return [], None
    finally:
        # Clean up temporary PDF file if created
        if pdf_path and temp_dir and os.path.exists(pdf_path):
            os.remove(pdf_path)