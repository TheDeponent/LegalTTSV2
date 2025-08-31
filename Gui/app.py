# ============================================================================
# LegalTTSV2 GUI Orchestrator
#
# This script provides the main GUI application for LegalTTSV2.
# It allows users to select a document (.docx or .pdf), choose an LLM model, system prompt,
# and voice, and then processes the document using LLM and TTS pipelines. The GUI displays
# progress for both LLM and audio processing, and produces a combined audio output. All business
# logic and processing is delegated to Core modules.
#
# Main Features:
# - Tkinter-based GUI for user interaction and settings selection
# - File selection for .docx or .pdf documents
# - Model, prompt, and voice selection
# - Progress bars for LLM and TTS steps
# - Calls Core modules for document processing, LLM, TTS, chunking, and audio concatenation
# - Cleans up intermediate audio files after combining
# - Handles errors and provides user feedback
# ============================================================================
import os
import re
from tkinter import messagebox
import threading
from dotenv import load_dotenv
from Core.llm_handler import get_llm_response
from Core.tts_handler import generate_speech
from Core.doc_handler import extract_text_from_docx
from Core.pdf_handler import process_pdf
from Core.constants import MAX_CHUNK_LENGTH
from Core.gui_utils import LegalTTSV2GUI, complete_progress_bar, update_progress_bar
from Core.prompt_handler import load_prompt, resolve_prompt_file
from Core.voice_assignment import assign_voices_to_chunks
from Core.audio_utils import play_audio

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


class LegalTTSV2:
    def on_submit(self):
        # Handler for the Start button. Disables the button, shows progress bars, and starts document processing in a thread.
        self.start_btn.config(state="disabled")
        # Reset progress bars to 0 at start
        update_progress_bar(self.llm_progress, 0)
        update_progress_bar(self.tts_progress, 0)
        # Start processing in a background thread
        threading.Thread(target=self._threaded_process_document, daemon=True).start()
    def __init__(self):
        # Initialize the LegalTTSV2GUI and expose all relevant GUI variables for compatibility.
        self.gui = LegalTTSV2GUI(self)
        self.root = self.gui.root
        self.button_frame = self.gui.button_frame
        self.frame = self.gui.frame
        self.selected_docx = self.gui.selected_docx
        self.selected_model = self.gui.selected_model
        self.selected_prompt = self.gui.selected_prompt
        self.selected_voice = self.gui.selected_voice
        self.voice_options = self.gui.voice_options
        self.model_options = self.gui.model_options
        self.prompt_options = self.gui.prompt_options
        self.skip_tts = self.gui.skip_tts
        self.llm_progress_label = self.gui.llm_progress_label
        self.llm_progress = self.gui.llm_progress
        self.tts_progress_label = self.gui.tts_progress_label
        self.tts_progress = self.gui.tts_progress
        self.start_btn = self.gui.start_btn
        self.custom_prompt_path = self.gui.custom_prompt_path
        self.use_custom_prompt = self.gui.use_custom_prompt

    def _threaded_process_document(self):
        # Main document processing workflow. Handles file conversion, LLM processing, chunking, TTS, audio concatenation,
        # and cleanup. Updates GUI progress bars throughout. All business logic is delegated to Core modules.
        # --- Gather user selections and file conversion (PDF/RTF to DOCX) ---
        docx_path = self.selected_docx.get()
        model_name = self.selected_model.get()
        system_prompt_key = self.selected_prompt.get()
        voice_name = self.selected_voice.get()
        # Use resolve_prompt_file to get the correct prompt file
        prompt_file = resolve_prompt_file(system_prompt_key, self.prompt_options, self.custom_prompt_path.get())
        llm_response = None
        temp_audio_files = []

        if docx_path.lower().endswith('.rtf'):
            print(f"Converting RTF to DOCX: {docx_path}")
            try:
                from Core.file_conversion import convert_rtf_to_docx
                docx_path = convert_rtf_to_docx(docx_path)
                print(f"Converted to DOCX: {docx_path}")
            except Exception as e:
                print(f"Failed to convert RTF to DOCX: {e}")
                self.root.after(0, self.processing_finished, False)
                return

        if docx_path.lower().endswith('.pdf'):
            print(f"Converting and preprocessing PDF: {docx_path}")
            # pdf_handler is used to convert and preprocess PDF files to DOCX format.
            docx_path = process_pdf(docx_path)

        # prompt_handler is used to load the selected system prompt from file.
        system_prompt = load_prompt(prompt_file)
        if prompt_file and not system_prompt:
            self.root.after(0, self.processing_finished, False)
            return

        # --- LLM and chunking logic ---
        if model_name == "no_model":
            # No LLM, just use document text
            complete_progress_bar(self.llm_progress)
            chunks_and_voices = []
        elif model_name in ["gemini-2.5-pro", "gemini-2.5-flash"]:
            # Gemini API (always upload file, get full response, then chunk for TTS)
            print(f"Using Gemini API model: {model_name}")
            from Core.gemini_handler import process_gemini_file_workflow
            all_voices = [v[0] for v in self.voice_options]
            chunks_and_voices, llm_response = process_gemini_file_workflow(
                docx_path,
                model_name,
                system_prompt,
                voice_name,
                all_voices,
                max_length=MAX_CHUNK_LENGTH
            )
            if chunks_and_voices is None:
                self.root.after(0, self.processing_finished, False)
                return
            update_progress_bar(self.llm_progress, 100)
        else:
            # doc_handler is used to extract text from the DOCX file, 
            # llm_handler is used to get the LLM response for the document.
            print(f"Extracting paragraph chunks from: {docx_path}")
            all_voices = [v[0] for v in self.voice_options]
            doc_text = extract_text_from_docx(docx_path)
            def llm_progress_cb(val):
                update_progress_bar(self.llm_progress, val)
            llm_response = get_llm_response(model_name, system_prompt, doc_text, progress_callback=llm_progress_cb)
            if not llm_response:
                self.root.after(0, self.processing_finished, False)
                return
            update_progress_bar(self.llm_progress, 100)
            # voice_assignment is used to assign voices to each chunk of the LLM response.
            chunks_and_voices = assign_voices_to_chunks(llm_response, voice_name, all_voices, max_length=MAX_CHUNK_LENGTH)

        # --- Prepare TTS progress bar ---
        total_chunks = len(chunks_and_voices)
        if not self.skip_tts.get():
            # Set maximum for progress bar (if needed)
            self.tts_progress['maximum'] = total_chunks
            update_progress_bar(self.tts_progress, 0)
        audio_segments = []
        tag_pattern = re.compile(r'<(/?AI SUMMARY|/?SPEAKER ?\d+)>', re.IGNORECASE)
        from Core.doc_chunking import split_long_paragraphs
        max_length = MAX_CHUNK_LENGTH
        # Flatten all sub-chunks to get the correct total
        flat_chunks = []
        for chunk, assigned_voice in chunks_and_voices:
            clean_chunk = tag_pattern.sub('', chunk).strip()
            # doc_chunking is used to split long paragraphs into smaller sub-chunks for TTS processing.
            sub_chunks = split_long_paragraphs([clean_chunk], max_length=max_length) if len(clean_chunk) > max_length else [clean_chunk]
            for sub_chunk in sub_chunks:
                flat_chunks.append((sub_chunk, assigned_voice))

        total_flat = len(flat_chunks)
        # --- TTS processing: Calls Core.tts_handler.generate_speech for each chunk ---
        for flat_idx, (sub_chunk, assigned_voice) in enumerate(flat_chunks):
            print(f"Processing chunk {flat_idx+1}/{total_flat} with voice {assigned_voice}")
            if not self.skip_tts.get():
                # tts_handler is used to generate speech audio for each text chunk using the assigned voice.
                audio_path = generate_speech(sub_chunk, assigned_voice)
                # Update the progress bar after each chunk is processed
                update_progress_bar(self.tts_progress, flat_idx + 1)
                if not audio_path:
                    print(f"Failed to generate audio for chunk {flat_idx+1}.")
                    continue
                temp_audio_files.append(audio_path)
                from pydub import AudioSegment
                seg = AudioSegment.from_wav(audio_path)
                audio_segments.append(seg)
                print(f"Chunk {flat_idx+1} audio duration: {seg.duration_seconds:.2f} seconds, file: {audio_path}")
        if not self.skip_tts.get():
            # Use gui_utils to set the progress bar to 100% (complete)
            complete_progress_bar(self.tts_progress)

        # --- Save LLM response to text file ---
        if llm_response:
            logs_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs"))
            os.makedirs(logs_dir, exist_ok=True)
            orig_base = os.path.splitext(os.path.basename(self.selected_docx.get()))[0]
            text_output_path = os.path.join(logs_dir, f"{orig_base}_LLMLOG.txt")
            try:
                with open(text_output_path, "w", encoding="utf-8") as f:
                    f.write(llm_response)
                print(f"AI response saved to: {text_output_path}")
            except Exception as e:
                print(f"Failed to save AI response: {e}")

        # --- Concatenate audio and clean up intermediate files ---
        if not self.skip_tts.get() and temp_audio_files:
            from Core.audio_utils import concatenate_and_cleanup_audio
            outputs_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs"))
            combined_path = concatenate_and_cleanup_audio(temp_audio_files, outputs_dir, self.selected_docx.get(), pause_ms=1000)
            cleaned_path = None
            # Automatically run STT deduplication on the generated WAV file
            try:
                from Core.audio_deduplication import auto_cleaned_filename, clean_audio_with_stt
                cleaned_path = auto_cleaned_filename(combined_path)
                clean_audio_with_stt(combined_path, cleaned_path, whisper_model="base.en")
            except Exception as e:
                print(f"STT deduplication failed: {e}")
                cleaned_path = None
            # Play the cleaned file if it exists, otherwise play the original
            from Core.audio_utils import play_audio
            play_target = cleaned_path if cleaned_path and os.path.exists(cleaned_path) else combined_path
            if play_target and os.path.exists(play_target):
                from pydub import AudioSegment
                audio = AudioSegment.from_wav(play_target)
                print(f"Final audio duration: {audio.duration_seconds:.2f} seconds, file: {play_target}")
                play_audio(play_target)

        self.root.after(0, self.processing_finished, True)

    def processing_finished(self, success):
        # Re-enables the UI after processing is complete, or closes the GUI if successful.
        self.start_btn.config(state="normal")
        # Hide progress bars after processing
        self.llm_progress_label.pack_forget()
        self.llm_progress.pack_forget()
        self.tts_progress_label.pack_forget()
        self.tts_progress.pack_forget()
        if success:
            self.root.after(500, self.root.destroy)  # Close GUI after a short delay
        else:
            messagebox.showerror("Error", "An error occurred during processing. Check the console for details.")

    def run(self):
        # Start the Tkinter main loop for the GUI.
        self.root.mainloop()
