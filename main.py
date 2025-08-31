# main.py
import sys
import os

# Add the project root to the Python path to ensure modules are found
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from Gui.app import LegalTTSV2

def main():
    """
    Main entry point for the LegalTTSV2 application.
    Initializes the GUI and starts the main event loop.
    """
    app = LegalTTSV2()
    app.run()

if __name__ == "__main__":
    # Check for the correct Python version if needed
    if sys.version_info[0] < 3:
        print("This application requires Python 3 or higher.")
        sys.exit(1)
    main()