from __future__ import annotations
from typing import Iterable
import gradio as gr
from Gui.app import process_document_backend
from Gui.app import VOICE_OPTIONS, MODEL_OPTIONS, PROMPT_OPTIONS
import traceback
import gradio.themes as themes
from gradio.themes.base import Base
from gradio.themes.utils import colors, fonts, sizes


voice_options = VOICE_OPTIONS
model_options = MODEL_OPTIONS + [("Custom", "__custom__")]
prompt_options = dict(PROMPT_OPTIONS)
PROMPT_LABELS = list(prompt_options.keys()) + ["Custom"]

def make_progress_html(label, percent):
    percent = int(percent)
    return f"""
    <div style='width:100%;margin-bottom:4px;'>{label}: {percent}%</div>
    <div style='width:100%;background:#222;height:18px;border-radius:6px;overflow:hidden;'>
      <div style='height:100%;width:{percent}%;background:#4caf50;transition:width 0.2s;'></div>
    </div>
    """

def gradio_process_document(input_file, model_name, prompt_key, voice_name, custom_prompt_text, skip_tts, llm_progress_html, tts_progress_html, custom_llm_model_name):
    try:
        logs_persistent = "Starting..."
        yield None, logs_persistent, make_progress_html("LLM", 0), make_progress_html("Audio", 0)
        # Accept both file and custom text input objects
        if hasattr(input_file, 'read') and hasattr(input_file, 'text'):
            # Custom text input object (from Custom LLM Input)
            input_file_path = input_file
        else:
            input_file_path = input_file.name if input_file else None
        if input_file_path is None:
            yield None, "No input file provided.", make_progress_html("LLM", 0), make_progress_html("Audio", 0)
            return
        if model_name == "Custom" or model_name == "__custom__":
            model_value = custom_llm_model_name.strip()
            if not model_value:
                yield None, "Please enter a custom LLM model name.", make_progress_html("LLM", 0), make_progress_html("Audio", 0)
                return
        else:
            model_value = next((v for (label, v) in model_options if label == model_name or v == model_name), model_name)
        voice_value = next((name for (name, desc) in voice_options if name == voice_name), voice_name)
        prompt_text = custom_prompt_text.strip() if custom_prompt_text else ""
        llm_progress_val = 0
        tts_progress_val = 0
        def llm_progress_cb(val):
            nonlocal llm_progress_val, logs_persistent
            llm_progress_val = val
            logs_persistent = f"LLM Progress: {llm_progress_val}%\n" + logs_persistent
        def tts_progress_cb(val):
            nonlocal tts_progress_val
            tts_progress_val = val
        audio_file_path = None
        for result in process_document_backend(
            input_file_path,
            model_value,
            "__custom__",
            voice_value,
            prompt_options,
            voice_options,
            prompt_text=prompt_text,
            skip_tts=skip_tts,
            progress=None,
            llm_progress_cb=llm_progress_cb,
            tts_progress_cb=tts_progress_cb
        ):
            if isinstance(result, tuple) and len(result) == 2:
                audio_file_path, log_line = result
                logs_persistent = f"{log_line}\n{logs_persistent}" if logs_persistent else log_line
            else:
                log_line = result
                logs_persistent = f"{log_line}\n{logs_persistent}" if logs_persistent else log_line
            yield None, logs_persistent, make_progress_html("LLM", llm_progress_val), make_progress_html("Audio", tts_progress_val)
        if audio_file_path and not skip_tts:
            yield audio_file_path, logs_persistent, make_progress_html("LLM", llm_progress_val), make_progress_html("Audio", tts_progress_val)
    except Exception as e:
        tb = traceback.format_exc()
        yield None, f"Error: {e}\n{tb}", make_progress_html("LLM", 0), make_progress_html("Audio", 0)



class RedOnBlack(Base):
    def __init__(
        self,
        *,
        primary_hue: colors.Color | str = colors.slate,  # slate for background/primary
        secondary_hue: colors.Color | str = colors.red,  # red for accents/buttons
        neutral_hue: colors.Color | str = colors.slate,
        spacing_size: sizes.Size | str = sizes.spacing_md,
        radius_size: sizes.Size | str = sizes.radius_md,
        text_size: sizes.Size | str = sizes.text_lg,
        font: fonts.Font | str | Iterable[fonts.Font | str] = (
            fonts.GoogleFont("Quicksand"),
            "ui-sans-serif",
            "sans-serif",
        ),
        font_mono: fonts.Font | str | Iterable[fonts.Font | str] = (
            fonts.GoogleFont("IBM Plex Mono"),
            "ui-monospace",
            "monospace",
        ),
    ):
        super().__init__(
            primary_hue=primary_hue,
            secondary_hue=secondary_hue,
            neutral_hue=neutral_hue,
            spacing_size=spacing_size,
            radius_size=radius_size,
            text_size=text_size,
            font=font,
            font_mono=font_mono,
        )
        super().set(
            # Use solid slate for background, red for buttons/accents
            body_background_fill="*primary_900",
            body_background_fill_dark="*primary_900",
            button_primary_background_fill="*secondary_500",
            button_primary_background_fill_hover="*secondary_400",
            button_primary_text_color="white",
            button_primary_background_fill_dark="*secondary_700",
            slider_color="*secondary_400",
            slider_color_dark="*secondary_700",
            block_title_text_weight="600",
            block_border_width="3px",
            block_shadow="*shadow_drop_lg",
            button_primary_shadow="*shadow_drop_lg",
            button_large_padding="40px",
        )

red_black_theme = RedOnBlack()

with gr.Blocks(theme=red_black_theme, css=None) as demo:
    gr.Markdown("# LegalTTSV2")
    with gr.Row():
        with gr.Column():
            llm_input_mode = gr.Dropdown(["Input Files", "Custom"], label="LLM Input", value="Input Files")
            input_file = gr.File(label="Select Input File (PDF, DOCX, RTF, TXT)", file_types=[".pdf", ".docx", ".rtf", ".txt"], visible=True)
            custom_input_text = gr.Textbox(label="Custom LLM Input Text", lines=8, visible=False)
            llm_model = gr.Dropdown([label for (label, value) in model_options], label="LLM Model", value=model_options[0][0])
            custom_llm_model_name = gr.Textbox(label="Custom LLM Model Name (Ollama)", lines=1, visible=False)
            prompt = gr.Dropdown(PROMPT_LABELS, label="Prompt Template", value="Custom")
            prompt_text = gr.Textbox(label="Prompt", lines=4, value="")
            voice = gr.Dropdown([name for (name, desc) in voice_options], label="Voice", value=voice_options[0][0])
            skip_tts = gr.Checkbox(label="Skip TTS (LLM only, no audio)", value=False)
            process_btn = gr.Button("Process and Export Audio", variant="primary")
        with gr.Column():
            llm_progress = gr.HTML(make_progress_html("LLM", 0))
            tts_progress = gr.HTML(make_progress_html("Audio", 0))
            audio_output = gr.Audio(label="Audio Output", interactive=False)
            logs_output = gr.Textbox(
                label="Logs / Status",
                lines=20,
                max_lines=20,
                autoscroll=True,
                elem_id="logs-status-box",
                container=True
            )



    def update_prompt_text(selected_prompt):
        if selected_prompt == "Custom":
            return gr.update(value="")
        return gr.update(value=prompt_options[selected_prompt])

    def show_custom_llm(selected_llm):
        return gr.update(visible=(selected_llm == "Custom"))
        
    def show_llm_input_mode(selected_mode):
        return (
            gr.update(visible=(selected_mode == "Input Files")),
            gr.update(visible=(selected_mode == "Custom"))
        )

    prompt.change(update_prompt_text, inputs=prompt, outputs=prompt_text)
    llm_model.change(show_custom_llm, inputs=llm_model, outputs=custom_llm_model_name)
    llm_input_mode.change(show_llm_input_mode, inputs=llm_input_mode, outputs=[input_file, custom_input_text])



    def gradio_process_document_llm_input(llm_input_mode_val, input_file, custom_input_text, llm_model_val, voice_val, prompt_text_val, skip_tts_val, llm_progress_val, tts_progress_val, custom_llm_model_name_val):
        # Always use prompt_text_val as the prompt, and pass '__custom__' as the prompt key
        if llm_input_mode_val == "Input Files":
            gen = gradio_process_document(input_file, llm_model_val, "__custom__", voice_val, prompt_text_val, skip_tts_val, llm_progress_val, tts_progress_val, custom_llm_model_name_val)
        else:
            class TextInputObj:
                def __init__(self, text):
                    self.name = None
                    self.text = text
                def read(self):
                    return self.text
            gen = gradio_process_document(TextInputObj(custom_input_text), llm_model_val, "__custom__", voice_val, prompt_text_val, skip_tts_val, llm_progress_val, tts_progress_val, custom_llm_model_name_val)
        for result in gen:
            yield result

    process_btn.click(
        gradio_process_document_llm_input,
        inputs=[llm_input_mode, input_file, custom_input_text, llm_model, voice, prompt_text, skip_tts, llm_progress, tts_progress, custom_llm_model_name],
        outputs=[audio_output, logs_output, llm_progress, tts_progress]
    )

    demo.launch(server_name="0.0.0.0")

import gradio as gr

