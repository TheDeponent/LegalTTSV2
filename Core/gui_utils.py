# ============================================================================
# gui_utils.py - GUI Utility Functions and Classes for LegalTTSV2
#
# This module provides the LegalTTSV2GUI class and utility functions for managing
# the Tkinter-based GUI of the RealTimeTTS LegalTTSV2 system. It handles all GUI
# widget creation, layout, and state management, including file selection,
# model, prompt, and voice selection, and progress bar controls. It also
# provides thread-safe utility functions for updating progress bars and showing
# error messages. All business logic and document processing is delegated to
# other Core modules; this module is responsible only for GUI presentation and
# user interaction.
# ============================================================================

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

class LegalTTSV2GUI:
    def __init__(self, app):
        # Initialize the LegalTTSV2GUI with all widgets and state variables
        self.app = app
        self.root = tk.Tk()
        self.root.title("LegalTTSV2 Settings")
        self.root.geometry("350x800")
        self.root.resizable(False, False)

        # Create main layout frames for content and buttons
        content_frame = tk.Frame(self.root)
        self.button_frame = tk.Frame(self.root)
        content_frame.pack(fill="both", expand=True)
        self.button_frame.pack(fill="x", side="bottom", pady=10, anchor="s")

        # Add a scrollable canvas for all options
        canvas = tk.Canvas(content_frame, borderwidth=0, background="#f0f0f0")
        self.frame = tk.Frame(canvas, background="#f0f0f0")
        vsb = tk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((0,0), window=self.frame, anchor="nw")

        # Configure scroll region when frame size changes
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        self.frame.bind("<Configure>", on_frame_configure)

        # Tkinter variables for user selections
        self.selected_docx = tk.StringVar()
        self.selected_model = tk.StringVar(value="no_model")
        self.selected_prompt = tk.StringVar(value="Legal (Summary Only)")
        self.selected_voice = tk.StringVar(value="Tara")

        # Voice options for selection in the GUI
        self.voice_options = [
            ("Tara", "Female, English, conversational, clear"),
            ("Leah", "Female, English, warm, gentle"),
            ("Jess", "Female, English, energetic, youthful"),
            ("Leo", "Male, English, authoritative, deep"),
            ("Dan", "Male, English, friendly, casual"),
            ("Mia", "Female, English, professional, articulate"),
            ("Zac", "Male, English, enthusiastic, dynamic"),
            ("Zoe", "Female, English, calm, soothing")
        ]

        # Model options for LLM selection
        self.model_options = [
            ("No Model", "no_model"),
            ("sushruth/solar-uncensored", "sushruth/solar-uncensored"),
            ("gemma3:1b", "gemma3:1b"),
            ("mistral:7b", "mistral:7b"),
            ("llama3:8b", "llama3:8b"),
            ("Gemini 2.5 Pro (API)", "gemini-2.5-pro"),
            ("Gemini 2.5 Flash (API)", "gemini-2.5-flash")
        ]

        # Prompt options for system prompt selection
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.prompt_options = {
            "Legal": os.path.join(project_root, "prompts", "legal.txt"),
            "Legal (Full Text)": os.path.join(project_root, "prompts", "legal (full text).txt"),
            "Legal (Summary Only)": os.path.join(project_root, "prompts", "legal (summary only).txt"),
            "Emotive": os.path.join(project_root, "prompts", "emotive.txt")
        }
        self.use_custom_prompt = tk.BooleanVar(value=False)
        self.custom_prompt_path = tk.StringVar(value="")

        # Boolean variable for skipping TTS
        self.skip_tts = tk.BooleanVar(value=False)

        # Create all widgets in the GUI
        self._create_widgets()

    def _create_widgets(self):
        # Create file selection widgets
        tk.Label(self.frame, text="Select .docx or .pdf file:").pack(pady=(20, 0), anchor="w", padx=40)
        tk.Button(self.frame, text="Browse", command=self.select_docx_or_pdf).pack(anchor="w", padx=40)
        tk.Label(self.frame, textvariable=self.selected_docx, wraplength=400, fg="blue", justify="left").pack(pady=(0, 10), anchor="w", padx=40)

        # Create model selection widgets
        tk.Label(self.frame, text="Choose Ollama Model:").pack(anchor="w", padx=40)
        for text, value in self.model_options:
            tk.Radiobutton(self.frame, text=text, variable=self.selected_model, value=value).pack(anchor="w", padx=40)

        # Create system prompt selection widgets
        tk.Label(self.frame, text="Choose System Prompt:").pack(pady=(10, 0), anchor="w", padx=40)
        for key in self.prompt_options:
            tk.Radiobutton(self.frame, text=key, variable=self.selected_prompt, value=key).pack(anchor="w", padx=40)
        # Custom prompt checkbox and file selector
        custom_frame = tk.Frame(self.frame)
        custom_frame.pack(anchor="w", padx=40, pady=(0,0), fill="x")
        tk.Checkbutton(custom_frame, text="Use Custom Prompt File", variable=self.use_custom_prompt, command=self._on_custom_prompt_toggle).pack(side="left")
        self.custom_prompt_label = tk.Label(custom_frame, textvariable=self.custom_prompt_path, wraplength=200, fg="blue", font=("Arial", 8))
        self.custom_prompt_label.pack(side="left", padx=(8,0))

        # Create voice selection widgets
        tk.Label(self.frame, text="Choose Voice:").pack(pady=(10, 0), anchor="w", padx=40)
        for name, desc in self.voice_options:
            vframe = tk.Frame(self.frame)
            vframe.pack(anchor="w", padx=40, pady=(0,0), fill="x")
            tk.Radiobutton(vframe, text=name, variable=self.selected_voice, value=name).pack(side="left")
            tk.Label(vframe, text=desc, font=("Arial", 8), fg="gray").pack(side="left", padx=(8,0))

        # Checkbox to skip TTS (audio generation)
        self.skip_tts_checkbox = tk.Checkbutton(self.frame, text="Skip TTS (LLM only, no audio)", variable=self.skip_tts)
        self.skip_tts_checkbox.pack(anchor="w", padx=40, pady=(10,0))

        # Progress bars and Start button (stacked vertically)
        self.llm_progress_label = tk.Label(self.button_frame, text="LLM Processing:")
        self.llm_progress = ttk.Progressbar(self.button_frame, orient="horizontal", length=250, mode="determinate")
        self.llm_progress_label.pack(fill="x", pady=(0,0))
        self.llm_progress.pack(fill="x", pady=(0,5))
        self.tts_progress_label = tk.Label(self.button_frame, text="Audio Generation:")
        self.tts_progress = ttk.Progressbar(self.button_frame, orient="horizontal", length=250, mode="determinate")
        self.tts_progress_label.pack(fill="x", pady=(0,0))
        self.tts_progress.pack(fill="x", pady=(0,10))
        # The Start button triggers the main workflow in the app (calls app.on_submit)
        self.start_btn = tk.Button(self.button_frame, text="Start", command=self.app.on_submit, bg="#4CAF50", fg="white", font=("Arial", 16, "bold"), height=2, width=12)
        self.start_btn.pack(pady=10)

    def select_docx_or_pdf(self):
        # filedialog is used to open a file selection dialog for .docx, .pdf, or .rtf files
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_dir = os.path.join(project_root, "Inputs")
        if not os.path.isdir(default_dir):
            default_dir = os.getcwd()
        file_path = filedialog.askopenfilename(
            title="Select a .docx, .pdf, or .rtf file",
            filetypes=[("Word Documents", "*.docx"), ("PDF Files", "*.pdf"), ("Rich Text Format", "*.rtf")],
            initialdir=default_dir
        )
        if file_path:
            self.selected_docx.set(file_path)

    def _on_custom_prompt_toggle(self):
        if self.use_custom_prompt.get():
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            default_dir = os.path.join(project_root, "prompts")
            file_path = filedialog.askopenfilename(
                title="Select a prompt file",
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
                initialdir=default_dir
            )
            if file_path:
                self.custom_prompt_path.set(file_path)
                self.selected_prompt.set("__custom__")
            else:
                self.use_custom_prompt.set(False)
        else:
            self.custom_prompt_path.set("")
            # Optionally reset to a default prompt
            if self.selected_prompt.get() == "__custom__":
                self.selected_prompt.set("Legal (Summary Only)")

    def run(self):
        self.root.mainloop()
def complete_progress_bar(progress_bar):
    # Instantly fill a Tkinter progress bar to 100% (used for LLM or TTS progress)
    progress_bar.after(0, progress_bar.config, {'value': progress_bar['maximum'] if 'maximum' in progress_bar.keys() else 100})

def update_progress_bar(progress_bar, value):
    # Thread-safe update for a Tkinter progress bar (used for LLM or TTS progress)
    progress_bar.after(0, progress_bar.config, {'value': value})

def show_error_messagebox(title, message):
    # messagebox is used to show an error dialog to the user
    messagebox.showerror(title, message)
