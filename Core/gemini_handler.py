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
try:
    import pypandoc
except Exception:
    pypandoc = None
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
            temp_dir = tempfile.gettempdir()
            pdf_path = None

            # Accept PDF directly
            if ext == '.pdf':
                pdf_path = input_path
                yield f"Using original PDF for Gemini upload: {os.path.basename(pdf_path)}"

            # DOCX -> PDF via Word automation/docx2pdf
            elif ext == '.docx':
                base = os.path.splitext(os.path.basename(input_path))[0]
                pdf_path = os.path.join(temp_dir, f"{base}_gemini_upload.pdf")
                yield f"Converting DOCX to PDF for Gemini upload: {os.path.basename(input_path)} -> {os.path.basename(pdf_path)}"
                try:
                    pythoncom.CoInitialize()
                    docx2pdf_convert(input_path, pdf_path)
                except Exception as e:
                    yield f"DOCX to PDF conversion failed: {e}"
                    yield [], None
                    return

            # RTF -> DOCX (pypandoc) -> PDF
            elif ext == '.rtf':
                if not pypandoc:
                    yield "pypandoc is required to convert RTF to DOCX before PDF upload. Aborting."
                    yield [], None
                    return
                base = os.path.splitext(os.path.basename(input_path))[0]
                docx_temp = os.path.join(temp_dir, f"{base}_temp.docx")
                pdf_path = os.path.join(temp_dir, f"{base}_gemini_upload.pdf")
                yield f"Converting RTF to DOCX (temp): {os.path.basename(input_path)} -> {os.path.basename(docx_temp)}"
                try:
                    pypandoc.convert_file(input_path, 'docx', outputfile=docx_temp)
                except Exception as e:
                    yield f"RTF to DOCX conversion failed: {e}"
                    yield [], None
                    return
                yield f"Converting DOCX to PDF for Gemini upload: {os.path.basename(docx_temp)} -> {os.path.basename(pdf_path)}"
                try:
                    pythoncom.CoInitialize()
                    docx2pdf_convert(docx_temp, pdf_path)
                except Exception as e:
                    yield f"DOCX to PDF conversion failed: {e}"
                    # cleanup docx_temp
                    if os.path.exists(docx_temp):
                        try:
                            os.remove(docx_temp)
                        except Exception:
                            pass
                    yield [], None
                    return

            else:
                yield f"Unsupported file type for Gemini upload: {ext}. Aborting."
                yield [], None
                return

            # Upload the PDF
            try:
                yield f"Uploading file to Gemini: {os.path.basename(pdf_path)}"
                uploaded_file = genai.upload_file(path=pdf_path, mime_type='application/pdf')
                prompt_parts.append(uploaded_file)
            except Exception as e:
                yield f"Failed to upload file to Gemini: {e}"
                yield [], None
                return

        elif input_text:
            prompt_parts.append(input_text)
        else:
            yield "No input provided (either file or text). Aborting."
            yield [], None
            return

        # --- 2. Generate Content from Gemini ---
        yield "Sending request to Gemini model..."
        response = model.generate_content(prompt_parts)

        # --- 3. Parse Response and Process for TTS ---
        llm_response = getattr(response, 'text', '')
        if isinstance(llm_response, str):
            llm_response = llm_response.strip()

        if not llm_response:
            yield "Gemini LLM response was empty."
            yield [], None
            return

        yield "Gemini response received. Chunking for TTS..."
        chunks_and_voices = assign_voices_to_chunks(llm_response, voice_name, all_voices, max_length=max_length)

        if not chunks_and_voices:
            yield "Gemini LLM response could not be chunked for TTS."
            yield [], llm_response
            return

        yield "Processing complete."
        yield chunks_and_voices, llm_response

    except Exception as e:
        error_message = f"An error occurred in the Gemini workflow: {e}"
        yield error_message
        yield [], None
    finally:
        # Clean up temporary files if created
        try:
            if 'docx_temp' in locals() and os.path.exists(docx_temp):
                os.remove(docx_temp)
        except Exception:
            pass
        try:
            if 'pdf_path' in locals() and pdf_path and os.path.exists(pdf_path) and pdf_path != input_path:
                os.remove(pdf_path)
        except Exception:
            pass