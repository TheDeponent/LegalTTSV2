# main.py - Entry point for LegalTTSV2 Gradio Web App
# Launches the Gradio interface for document-to-audio processing.

import sys
import os
from Core.llm_handler import log

# Add the project root to the Python path to ensure modules are found
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def main():
    # Main entry point for the LegalTTSV2 Gradio web application.
    try:
        from Gui import gradio_app
        log("Launching Gradio app...")
        gradio_app.launch()
    except Exception as e:
        log(f"Failed to launch Gradio app: {e}")
        raise

if __name__ == "__main__":
    if sys.version_info[0] < 3:
        log("This application requires Python 3 or higher.")
        sys.exit(1)
    main()