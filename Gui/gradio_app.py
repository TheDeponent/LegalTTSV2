
import gradio as gr
from Gui.app import process_document_backend
from Gui.app import VOICE_OPTIONS, MODEL_OPTIONS, PROMPT_OPTIONS
import traceback

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
        input_file_path = input_file.name if input_file else None
        if not input_file_path:
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
        if prompt_key == "Custom":
            prompt_key_value = "__custom__"
            custom_prompt_path = custom_prompt_text.strip()
            if not custom_prompt_path:
                yield None, "Please enter a custom prompt.", make_progress_html("LLM", 0), make_progress_html("Audio", 0)
                return
        else:
            prompt_key_value = prompt_key
            custom_prompt_path = None
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
            prompt_key_value,
            voice_value,
            prompt_options,
            voice_options,
            custom_prompt_path=custom_prompt_path,
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


with gr.Blocks() as demo:
    gr.Markdown("# LegalTTSV2")
    with gr.Row():
        with gr.Column():
            input_file = gr.File(label="Select Input File (PDF, DOCX, RTF)")
            llm_model = gr.Dropdown([label for (label, value) in model_options], label="LLM Model", value=model_options[0][0])
            custom_llm_model_name = gr.Textbox(label="Custom LLM Model Name (Ollama)", lines=1, visible=False)
            prompt = gr.Dropdown(PROMPT_LABELS, label="Prompt", value=PROMPT_LABELS[0])
            custom_prompt_text = gr.Textbox(label="Custom Prompt Text (enter your prompt here)", lines=4, visible=False)
            voice = gr.Dropdown([name for (name, desc) in voice_options], label="Voice", value=voice_options[0][0])
            skip_tts = gr.Checkbox(label="Skip TTS (LLM only, no audio)", value=False)
            process_btn = gr.Button("Process and Export Audio")
        with gr.Column():
            llm_progress = gr.HTML(make_progress_html("LLM", 0), label="LLM Progress")
            tts_progress = gr.HTML(make_progress_html("Audio", 0), label="Audio Progress")
            audio_output = gr.Audio(label="Audio Output", interactive=False)
            logs_output = gr.Textbox(label="Logs / Status", lines=15)


    def show_custom_prompt(selected_prompt):
        return gr.update(visible=(selected_prompt == "Custom"))
    def show_custom_llm(selected_llm):
        return gr.update(visible=(selected_llm == "Custom"))

    prompt.change(show_custom_prompt, inputs=prompt, outputs=custom_prompt_text)
    llm_model.change(show_custom_llm, inputs=llm_model, outputs=custom_llm_model_name)

    process_btn.click(
        gradio_process_document,
        inputs=[input_file, llm_model, prompt, voice, custom_prompt_text, skip_tts, llm_progress, tts_progress, custom_llm_model_name],
        outputs=[audio_output, logs_output, llm_progress, tts_progress]
    )

    demo.launch()
