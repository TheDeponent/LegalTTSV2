# ============================================================================
# app.py - Gradio Orchestrator for LegalTTSV2
#
# Provides the main backend logic for the Gradio web interface of LegalTTSV2.
# Handles all document-to-audio processing, including LLM, TTS, chunking, deduplication,
# and progress reporting. No GUI or user interaction code; designed for use in the Gradio pipeline.
# ============================================================================


import os
import re
import time
from pydub import AudioSegment
from dotenv import load_dotenv
from Core.llm_handler import get_llm_response
from Core.tts_handler import generate_speech
from Core.doc_utils import extract_text_from_docx, convert_to_docx, split_long_paragraphs
from Core.constants import MAX_CHUNK_LENGTH
from Core.prompt_handler import get_system_prompt
from Core.voice_assignment import assign_voices_to_chunks
from Core.audio_deduplication import auto_cleaned_filename, clean_audio_with_stt
from Core.audio_utils import concatenate_and_cleanup_audio
from Core.gemini_handler import process_gemini_file_workflow
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# Gradio UI options/constants
VOICE_OPTIONS = [
    ("Tara", "Female, English, conversational, clear"),
    ("Leah", "Female, English, warm, gentle"),
    ("Jess", "Female, English, energetic, youthful"),
    ("Leo", "Male, English, authoritative, deep"),
    ("Dan", "Male, English, friendly, casual"),
    ("Mia", "Female, English, professional, articulate"),
    ("Zac", "Male, English, enthusiastic, dynamic"),
    ("Zoe", "Female, English, calm, soothing")
]

MODEL_OPTIONS = [
    ("No Model", "no_model"),
    ("sushruth/solar-uncensored", "sushruth/solar-uncensored"),
    ("gemma3:1b", "gemma3:1b"),
    ("mistral:7b", "mistral:7b"),
    ("llama3:8b", "llama3:8b"),
    ("Gemini 2.5 Pro (API)", "gemini-2.5-pro"),
    ("Gemini 2.5 Flash (API)", "gemini-2.5-flash")
]


project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
prompts_dir = os.path.join(project_root, "Prompts")
PROMPT_OPTIONS = {}
if os.path.isdir(prompts_dir):
    for fname in os.listdir(prompts_dir):
        if fname.lower().endswith(".txt"):
            prompt_name = os.path.splitext(fname)[0]
            prompt_path = os.path.join(prompts_dir, fname)
            try:
                with open(prompt_path, "r", encoding="utf-8") as f:
                    PROMPT_OPTIONS[prompt_name] = f.read()
            except Exception as e:
                PROMPT_OPTIONS[prompt_name] = f"[Error loading prompt: {e}]"

def process_document_backend(
    input_file_path,
    model_name,
    system_prompt_key,
    voice_name,
    prompt_options,
    voice_options,
    prompt_text=None,
    skip_tts=False,
    progress=None,
    llm_progress_cb=None,
    tts_progress_cb=None
):


    # Convert input file to DOCX if needed (handles RTF, PDF, DOCX)
    temp_audio_files = []
    llm_response = None
    system_prompt, prompt_status = get_system_prompt(system_prompt_key, prompt_options, prompt_text)
    yield prompt_status
    if not system_prompt:
        return

    # --- Custom LLM Input Bypass for ALL Models ---
    is_custom_text = hasattr(input_file_path, 'read') and hasattr(input_file_path, 'text')
    custom_text = input_file_path.text if is_custom_text else None

    if is_custom_text:
        # Custom text input: skip all file conversion and extraction logic
        # For Gemini, send prompt as system_prompt and user text as input
        if model_name in ["gemini-2.5-pro", "gemini-2.5-flash"]:
            from Core.gemini_handler import get_gemini_response
            yield f"[Gemini] System prompt being sent: {repr(system_prompt)}"
            yield f"[Gemini] User text being sent: {repr(custom_text)}"
            yield "Sending custom text (with prompt) directly to Gemini API..."
            if llm_progress_cb:
                llm_progress_cb(10)
            elif progress:
                progress(10, desc="LLM: Sending custom text to Gemini API...")
            # Patch: set a log callback so Gemini API output goes to Gradio log
            gemini_logs = []
            def gemini_log(msg):
                gemini_logs.append(f"Gemini: {msg}")
            get_gemini_response.log_callback = gemini_log
            llm_response = get_gemini_response(custom_text, model_name, system_prompt, GOOGLE_API_KEY)
            get_gemini_response.log_callback = None
            for log_msg in gemini_logs:
                yield log_msg
            if not llm_response:
                yield "Gemini API returned no response for custom text."
                return
            yield f"[Gemini LLM Response]\n{llm_response.strip()}"
        else:
            # For Ollama or other models, use get_llm_response generator
            yield "Sending custom text to LLM..."
            combined_input = f"{system_prompt}\n\n{custom_text}" if system_prompt else custom_text
            def _llm_progress(val):
                if llm_progress_cb:
                    llm_progress_cb(val)
                elif progress:
                    progress(val, desc=f"LLM: Processing ({val}%)")
            llm_response = ""
            for chunk in get_llm_response(model_name, None, combined_input, progress_callback=_llm_progress):
                if isinstance(chunk, str) and not chunk.startswith("LLM Logs:"):
                    llm_response += chunk
            if not llm_response:
                yield "LLM processing failed."
                return
            yield f"[LLM Response]\n{llm_response.strip()}"
        all_voices = [v[0] for v in voice_options]
        chunks_and_voices = assign_voices_to_chunks(llm_response, voice_name, all_voices, max_length=MAX_CHUNK_LENGTH)
        if llm_progress_cb:
            llm_progress_cb(100)
        elif progress:
            progress(100, desc="LLM: Complete.")
        yield f"LLM processing complete. {len(chunks_and_voices)} chunks ready for TTS."

    else:
        # Only run file-based logic if not in custom text mode
        try:
            docx_path = convert_to_docx(input_file_path)
            if docx_path != input_file_path:
                yield f"Converted to: {docx_path}"
        except ValueError as ve:
            yield (f"Invalid file type. Only PDF, DOCX, RTF, and TXT files are allowed.\nDetails: {ve}")
            return
        except Exception as e:
            yield f"File conversion failed: {e}"
            return

        # --- Unified LLM/Chunking logic for all models ---
        all_voices = [v[0] for v in voice_options]
        chunks_and_voices = []
        llm_response = None
        if model_name == "no_model":
            yield "No LLM model selected, skipping LLM step."
            if llm_progress_cb:
                llm_progress_cb(100)
            elif progress:
                progress(100, desc="LLM: No model selected, skipping.")
        elif model_name in ["gemini-2.5-pro", "gemini-2.5-flash"]:
            yield "Sending document to Gemini API..."
            if llm_progress_cb:
                llm_progress_cb(10)
            elif progress:
                progress(10, desc="LLM: Sending to Gemini API...")
            chunks_and_voices, llm_response, gemini_debug_logs = process_gemini_file_workflow(
                docx_path,
                model_name,
                system_prompt,
                voice_name,
                all_voices,
                max_length=MAX_CHUNK_LENGTH
            )
            for dbg in gemini_debug_logs:
                yield dbg
            if llm_progress_cb:
                llm_progress_cb(100)
            elif progress:
                progress(100, desc="LLM: Gemini response received.")
            if not chunks_and_voices:
                if llm_response and llm_response.strip():
                    yield "Gemini LLM response could not be chunked for TTS. Check prompt or input formatting."
                    yield f"Gemini LLM response (truncated): {llm_response[:500]}..."
                else:
                    yield "Gemini processing failed or returned no response."
                return
            if not isinstance(chunks_and_voices, list) or not all(isinstance(x, (tuple, list)) and len(x) == 2 for x in chunks_and_voices):
                yield f"Gemini returned malformed chunk list: {chunks_and_voices}"
                return
            yield f"Gemini LLM processing complete. {len(chunks_and_voices)} chunks ready for TTS."
        else:
            doc_text = extract_text_from_docx(docx_path)
            yield "Extracted text from DOCX. Running LLM..."
            def _llm_progress(val):
                if llm_progress_cb:
                    llm_progress_cb(val)
                elif progress:
                    progress(val, desc=f"LLM: Processing ({val}%)")
            llm_response_gen = get_llm_response(model_name, system_prompt, doc_text, progress_callback=_llm_progress)
            llm_response = ""
            for chunk in llm_response_gen:
                if isinstance(chunk, str) and not chunk.startswith("LLM Logs:"):
                    llm_response += chunk
            if not llm_response:
                yield "LLM processing failed."
                return
            yield "LLM response received. Assigning voices to chunks..."
            chunks_and_voices = assign_voices_to_chunks(llm_response, voice_name, all_voices, max_length=MAX_CHUNK_LENGTH)
            if llm_progress_cb:
                llm_progress_cb(100)
            elif progress:
                progress(100, desc="LLM: Complete.")
            yield "Voice assignment complete."

    # --- Prepare TTS chunks and run TTS/audio for all models ---
    if not chunks_and_voices:
        yield "No valid chunks for TTS."
        return
    tag_pattern = re.compile(r'<(/?AI SUMMARY|/?SPEAKER ?\d+)>', re.IGNORECASE)
    max_length = MAX_CHUNK_LENGTH
    flat_chunks = []
    for idx, (chunk, assigned_voice) in enumerate(chunks_and_voices):
        clean_chunk = tag_pattern.sub('', chunk).strip()
        # Split only if needed, otherwise just use the chunk
        if len(clean_chunk) > max_length:
            sub_chunks = split_long_paragraphs([clean_chunk], max_length=max_length)
            for sub_chunk in sub_chunks:
                flat_chunks.append((sub_chunk, assigned_voice))
        else:
            flat_chunks.append((clean_chunk, assigned_voice))
        # Log chunk number and character count
        yield f"Chunk {idx+1}: {len(clean_chunk)} characters | Voice: {assigned_voice}"

    # TTS processing (moved outside the chunk loop)
    audio_segments = []
    tts_fail_count = 0
    if not skip_tts:
        import time
        total_tts = len(flat_chunks)
        for flat_idx, (sub_chunk, assigned_voice) in enumerate(flat_chunks):
            def per_chunk_progress(val):
                base = int(100 * flat_idx / total_tts)
                next_base = int(100 * (flat_idx + 1) / total_tts)
                mapped = base + int((next_base - base) * val / 100)
                if tts_progress_cb:
                    tts_progress_cb(mapped)
                elif progress:
                    progress(mapped, desc=f"TTS: {flat_idx+1}/{total_tts} audio chunks done")
            yield f"Generating speech for chunk {flat_idx+1}/{total_tts} (voice: {assigned_voice})..."
            audio_path = generate_speech(sub_chunk, assigned_voice, progress_callback=per_chunk_progress)
            if not audio_path:
                tts_fail_count += 1
                yield f"TTS failed for chunk {flat_idx+1}. Skipping."
                continue
            temp_audio_files.append(audio_path)
            seg = AudioSegment.from_wav(audio_path)
            audio_segments.append(seg)
            # Wait briefly to ensure TTS server is ready for next chunk
            time.sleep(0.2)
        if tts_fail_count == total_tts:
            yield "All TTS requests failed. No audio was generated. Please check the Orpheus TTS server and logs."
        else:
            yield "TTS complete."


        # Save LLM response to text file
        if hasattr(input_file_path, 'read') and hasattr(input_file_path, 'text'):
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            orig_base = f"custom_input_{timestamp}"
        else:
            orig_base = os.path.splitext(os.path.basename(input_file_path))[0]
        logs_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs"))
        os.makedirs(logs_dir, exist_ok=True)
        text_output_path = os.path.join(logs_dir, f"{orig_base}_LLMLOG.txt")
        if llm_response:
            try:
                with open(text_output_path, "w", encoding="utf-8") as f:
                    f.write(llm_response)
                yield f"LLM response saved to: {text_output_path}"
            except Exception as e:
                yield f"Failed to save AI response: {e}"

        # Concatenate audio and clean up intermediate files
        if not skip_tts and temp_audio_files:
            outputs_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs"))
            yield "Concatenating audio and cleaning up intermediate files..."
            # Use a generic name for custom input
            audio_base = orig_base if orig_base else "output"
            combined_path = concatenate_and_cleanup_audio(temp_audio_files, outputs_dir, audio_base, pause_ms=1000)
            cleaned_path = None
            cleaned_created = False
            try:
                cleaned_path = auto_cleaned_filename(combined_path)
                yield f"Running audio deduplication (Whisper STT)..."
                for msg in clean_audio_with_stt(combined_path, cleaned_path, whisper_model="base.en"):
                    yield msg
                # If deduplication actually created a new file, mark it
                if os.path.exists(cleaned_path) and os.path.getmtime(cleaned_path) > os.path.getmtime(combined_path):
                    cleaned_created = True
            except Exception as e:
                yield f"Audio deduplication failed: {e}"
                cleaned_path = None
            # Only use cleaned_path if it was actually created in this run
            play_target = cleaned_path if cleaned_created else combined_path
            if play_target and os.path.exists(play_target):
                yield (play_target, f"Audio generated: {play_target}\nLLM log: {text_output_path}")
                return
            else:
                yield (None, "Audio generation failed.")
                return
        else:
            yield (None, f"LLM log: {text_output_path}")
            return

