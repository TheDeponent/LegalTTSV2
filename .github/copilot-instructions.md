
# Copilot Instructions for LegalTTSV2

## Project Overview
LegalTTSV2 is a modular, Gradio web-based pipeline for converting legal documents (PDF, DOCX, RTF) to audio using LLMs (Ollama, Gemini) and Orpheus TTS, with features for audio deduplication and voice assignment. The system is designed for summarising Australian legal judgments and optimizing them for audio listening, but supports custom prompts and flexible workflows.

## Architecture & Key Components
- **Entry Point:** `main.py` launches the Gradio web UI (`gradio_app.py`).
- **Web UI:** `gradio_app.py` (Gradio interface, progress, logs, audio output), `Gui/app.py` (workflow orchestrator, generator-based streaming).
- **Core Logic:** All business logic is in `Core/` (TTS, LLM, chunking, deduplication, etc). Key modules:
  - `tts_handler.py`: Orpheus TTS API integration (endpoint via `.env` as `TTS_ENDPOINT`).
  - `llm_handler.py`: Handles LLM calls (Ollama, Gemini). Gemini always uploads the file and chunks after response.
  - `gemini_handler.py`: Gemini API file upload and response.
  - `audio_deduplication.py`: Uses Whisper STT to remove repeated audio segments.
  - `voice_assignment.py`: Assigns voices to text chunks (tag-based or round-robin).
  - `doc_chunking.py`, `doc_handler.py`, `pdf_handler.py`, `file_conversion.py`: Document parsing and conversion utilities.
- **Prompts:** Stored in `Prompts/`, selectable/customizable via web UI.
- **File Handling:** Inputs in `Inputs/`, outputs in `Outputs/`, logs in `logs/`, text outputs in `Text Outputs/`.

## Developer Workflows
- **Run the App:**
  - `python main.py` (Python 3.8+, see `.env` and `requirements.txt` for dependencies)
- **Environment:**
  - Set `TTS_ENDPOINT` in `.env` (e.g., `http://localhost:5005/v1/audio/speech`).
  - Set `GOOGLE_API_KEY` for Gemini API use.
  - Ollama must be running for Ollama models (`ollama serve`).
- **Testing:**
  - No formal test suite; test via Gradio UI and sample documents.
- **Build/Dependencies:**
  - Install with `pip install -r requirements.txt`.
  - Orpheus TTS server must be running (see [Lex-au/Orpheus-FastAPI](https://github.com/Lex-au/Orpheus-FastAPI)).

## Project Conventions & Patterns
- **Separation of Concerns:** Business logic in `Core/`, web UI in `gradio_app.py` and `Gui/app.py`.
- **Prompt Selection:** Use `resolve_prompt_file()` to get the correct prompt file path (handles custom prompts).
- **Audio Deduplication:** Always run deduplication after audio concatenation (`audio_deduplication.py`).
- **File Handling:** All intermediate/output files in `Outputs/`, `logs/`, `Text Outputs/`.
- **.gitignore:** `.env`, `ZZZ_Archive/`, and all files in `Inputs/`, `logs/`, and `outputs/` are ignored by git.

## Integration Points
- **External Services:**
  - Orpheus TTS (HTTP API, endpoint configurable)
  - Gemini API (requires Google API key)
- **Document Conversion:**
  - Uses `win32com` for DOCX/PDF conversion (Windows only)
  - Uses `pypandoc` for RTF to DOCX

## Examples
- To add a new LLM, implement a handler in `Core/llm_handler.py` and update the model options in the web UI.
- To add a new prompt, place a `.txt` file in `Prompts/` and it will appear in the UI.

---
If any conventions or workflows are unclear, please ask for clarification or examples before making major changes.
