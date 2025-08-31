# Copilot Instructions for LegalTTSV2

## Project Overview
- **Purpose:** LegalTTSV2 is a modular, GUI-driven pipeline for document-to-audio conversion using LLMs (Ollama, Gemini) and Orpheus TTS, with audio deduplication and voice assignment. The intended use case is to summarise Australian legal judgments, and tools are provided to optimise the text of judgments for audio listening. However, you are able to select custom prompts to generate different responses via a simplified workflow if necessary.
- **Architecture:**
  - `main.py` launches the GUI (`Gui/app.py`), which orchestrates the workflow.
  - All business logic is in `Core/` modules, separated by concern (TTS, LLM, chunking, deduplication, etc).
  - GUI logic is in `Core/gui_utils.py` (Tkinter-based), with user selections passed to the app orchestrator.
  - Prompts are stored in `Prompts/` and can be selected or customized via the GUI.

## Key Components
- **Core Modules:**
  - `tts_handler.py`: Sends text to Orpheus TTS (endpoint set via `.env` as `TTS_ENDPOINT`).
  - `llm_handler.py`: Handles LLM calls (Ollama, Gemini). Gemini always uploads the file and chunks after response.
  - `gemini_handler.py`: Handles Gemini API file upload and response.
  - `audio_deduplication.py`: Uses Whisper STT to remove repeated audio segments.
  - `voice_assignment.py`: Assigns voices to text chunks, using tags or round-robin.
  - `doc_chunking.py`, `doc_handler.py`, `pdf_handler.py`, `file_conversion.py`: Document parsing and conversion utilities.
- **GUI:**
  - `Gui/app.py` and `Core/gui_utils.py` define all user interaction and workflow triggers.
  - Users can select input files, LLM model, prompt, and voice, and optionally provide a custom prompt file.

## Developer Workflows
- **Run the App:**
  - `python main.py` (requires Python 3.8+, see `.env` and `requirements.txt` for dependencies)
- **Environment:**
  - Set `TTS_ENDPOINT` in `.env` (e.g., `http://localhost:5005/v1/audio/speech`).
  - Set `GOOGLE_API_KEY` for Gemini API use.
- **Testing:**
  - No formal test suite; test by running the GUI and processing sample documents.
- **Build/Dependencies:**
  - Install with `pip install -r requirements.txt`.
  - Orpheus TTS server must be running - this project is intended for use with https://github.com/Lex-au/Orpheus-FastAPI/blob/  main/LICENSE - my thanks to the creators of Orpheus and Lex-au who provided the API.
  - Ollama must be running to use the ollama models specified in the project. If you have Ollama installed, run it in a terminal with 'ollama serve'

## Project Conventions & Patterns
- **Separation of Contents:** All business logic is in `Core/`, GUI in `Gui/` and `Core/gui_utils.py`.
- **Prompt Selection:** Use `resolve_prompt_file()` to get the correct prompt file path (handles custom prompts).
- **Audio Deduplication:** Always run deduplication after audio concatenation; see `audio_deduplication.py` for details.
- **File Handling:** All intermediate and output files are stored in `Outputs/`, `logs/`, and `Text Outputs/`.
- **.gitignore:** `.env`, `ZZZ_Archive/`, and all files in `Inputs/`, `logs/`, and `outputs/` are ignored by git.

## Integration Points
- **External Services:**
  - Orpheus TTS (HTTP API, endpoint configurable)
  - Gemini API (requires Google API key)
- **Document Conversion:**
  - Uses `win32com` for DOCX/PDF conversion (Windows only)
  - Uses `pypandoc` for RTF to DOCX

## Examples
- To add a new LLM, implement a handler in `Core/llm_handler.py` and update the GUI model options.
- To add a new prompt, place a `.txt` file in `Prompts/` and it will appear in the GUI.

---

If any conventions or workflows are unclear, please ask the user for clarification or examples before proceeding with major changes.
