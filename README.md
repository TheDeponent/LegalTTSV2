# LegalTTSV2

LegalTTSV2 is a modular, GUI-driven pipeline for converting legal documents to audio using LLMs (Ollama, Gemini) and Orpheus TTS, with features for audio deduplication and voice assignment. It is designed to summarise Australian legal judgments and optimize them for audio listening, but also supports custom prompts and workflows.

## Features
- **Document-to-Audio Pipeline:** Convert legal documents (PDF, DOCX, RTF) to audio files.
- **LLM Integration:** Supports Ollama and Gemini for summarization and text processing.
- **Orpheus TTS:** Uses Orpheus TTS via HTTP API (endpoint configurable in `.env`).
- **Audio Deduplication:** Removes repeated audio segments using Whisper STT.
- **Voice Assignment:** Assigns voices to text chunks (tag-based or round-robin).
- **Prompt Selection:** Choose or customize prompts for LLMs via the GUI.
- **GUI:** Tkinter-based interface for file selection, model/prompt/voice choice, and workflow control.

## Architecture
- **Entry Point:** `main.py` launches the GUI (`Gui/app.py`).
- **Core Logic:** All business logic is in `Core/` (TTS, LLM, chunking, deduplication, etc).
- **GUI Logic:** In `Core/gui_utils.py` and `Gui/app.py`.
- **Prompts:** Stored in `Prompts/`, selectable/customizable via GUI.
- **File Handling:** Inputs in `Inputs/`, outputs in `Outputs/`, logs in `logs/`, text outputs in `Text Outputs/`.

## Setup & Usage
0. (Optional) Initialise a virtual environment:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
1. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```
   - FFMPEG is also required (https://ffmpeg.org/download.html) and must be added to your PATH.
2. **Configure environment:**
   - Create a .env file with New-Item -Path .env.env -ItemType File
   - Set `TTS_ENDPOINT` in `.env` (e.g., `http://localhost:5005/v1/audio/speech`).
   - Set `GOOGLE_API_KEY` for Gemini API use.
3. **Run Orpheus TTS server:**
   - See [Orpheus-FastAPI](https://github.com/Lex-au/Orpheus-FastAPI) for setup.
   - Once set up, users with CUDA-enabled graphics cards can use the following commands to run the server via docker and prepare for use:
   ```powershell
   cd Orpheus-FastAPI
   docker compose -f docker-compose-gpu.yml up
   ```
4. **Run Ollama (if using Ollama models):**
   ```powershell
   ollama serve
   ```
5. **Start the app:**
   ```powershell
   python main.py
   ```
6. **Use the GUI:**
   - Select input file, LLM model, prompt, and voice.
   - Optionally provide a custom prompt file.
   - Process and export audio.

## Developer Notes
- **Add a new LLM:** Implement a handler in `Core/llm_handler.py` and update GUI model options.
- **Add a new prompt:** Place a `.txt` file in `Prompts/` and select the prompt when running the app.
- **Audio deduplication:** Always run after audio concatenation (`audio_deduplication.py`).
- **Document conversion:** Uses `win32com` for DOCX/PDF (Windows only), `pypandoc` for RTF to DOCX.
- **Testing:** No formal test suite; test via GUI and sample documents.
- **Docx Conversion:** For conversion of PDF -> Docx, the scripts will attempt to convert via word for optimal conversion, but will fall back to a python-based conversion via pdf2docx if Word is unavailable.

## Project Conventions
- **Separation of concerns:** Business logic in `Core/`, GUI in `Gui/` and `Core/gui_utils.py`.
- **.gitignore:** `.env`, `ZZZ_Archive/`, and all files in `Inputs/`, `logs/`, and `outputs/` are ignored by git.

## Credits
- Orpheus TTS API by [Lex-au/Orpheus-FastAPI](https://github.com/Lex-au/Orpheus-FastAPI)
- Orpheus TTS (https://github.com/canopyai/Orpheus-TTS)

## Known Issues
- The progress bars for LLMs update inconsistently

---
If you have questions about conventions or workflows, please ask for clarification or examples before making major changes.
