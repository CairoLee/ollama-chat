import gradio as gr
from ollama import Client as ollama


def work_in_progress():
    gr.Warning("This feature is still under development.")


def parse_to_dict(text) -> dict:
    # 以换行符分割文本获取每行
    lines = text.strip().split("\n")
    result_dict = {}

    # 遍历每行，分割键和值，并加入字典
    for line in lines:
        key, value = line.split(maxsplit=1)
        # 处理值，转换为适当的数据类型
        try:
            # 尝试将值转换为float，失败则保持原样
            converted_value = float(value)
            # 如果值是整数，转换为int类型
            if converted_value.is_integer():
                converted_value = int(converted_value)
            value = converted_value
        except ValueError:
            pass

        # 如果键已存在（如示例中的'stop'），则转换为list存储多个值
        if key in result_dict:
            if not isinstance(result_dict[key], list):
                result_dict[key] = [result_dict[key]]
            result_dict[key].append(value)
        else:
            result_dict[key] = value

    return result_dict


def fetch_models(base_url):
    if base_url is None or len(base_url) == 0:
        gr.Warning("Base URL is required.")
        return gr.update(choices=[], value=None)

    try:
        client = ollama(host=base_url)
        response = client.list()
    except Exception as e:
        gr.Error(f"Failed to fetch models: {e}")
        return gr.update(choices=[], value=None)

    model_names = [model["name"] for model in response["models"]]
    return gr.update(
        choices=model_names, value=None if len(model_names) == 0 else model_names[0]
    )


def fetch_params(base_url, model_name):
    if base_url is None or len(base_url) == 0:
        gr.Warning("Base URL is required.")
        return 2048, 0.8, 40, 0.9, 1.1, 64

    if model_name is None or len(model_name) == 0:
        gr.Warning("Model name is required.")
        return 2048, 0.8, 40, 0.9, 1.1, 64

    try:
        client = ollama(host=base_url)
        response = client.show(model_name)
    except Exception as e:
        gr.Error(f"Failed to fetch model parameters: {e}")

    if "parameters" not in response:
        raise gr.Error("Model does not have parameters.")

    params = parse_to_dict(response["parameters"])
    if params is None:
        raise gr.Error("Failed to parse model parameters.")

    max_tokens = params.get("num_ctx", 2048)
    temperature = params.get("temperature", 0.8)
    top_k = params.get("top_k", 40)
    top_p = params.get("top_p", 0.9)
    repeat_penalty = params.get("repeat_penalty", 1.1)
    repeat_last_n = params.get("repeat_last_n", 64)

    return max_tokens, temperature, top_k, top_p, repeat_penalty, repeat_last_n


def do_chat(
    message,
    history,
    base_url,
    model_name,
    system_prompt,
    temperature,
    top_p,
    max_tokens,
    top_k,
    repeat_penalty,
    repeat_last_n,
):
    client = ollama(host=base_url)

    history_openai_format = []

    # 添加系统提示词
    if system_prompt is not None and system_prompt != "":
        history_openai_format.append({"role": "system", "content": system_prompt})

    # 添加历史对话
    for human, assistant in history:
        history_openai_format.append({"role": "user", "content": human})
        history_openai_format.append({"role": "assistant", "content": assistant})

    # 添加本次用户输入
    history_openai_format.append({"role": "user", "content": message})

    # 调用 ollama 的 SDK 接口进行对话
    response = client.chat(
        model=model_name,
        messages=history_openai_format,
        stream=True,
        options={
            "temperature": temperature,
            "num_ctx": max_tokens,
            "top_p": top_p,
            "top_k": top_k,
            "repeat_penalty": repeat_penalty,
            "repeat_last_n": repeat_last_n,
        },
    )

    partial_message = ""
    for chunk in response:
        if chunk["message"]["content"] is not None:
            partial_message = partial_message + chunk["message"]["content"]
            yield partial_message


chatbot = gr.Chatbot(
    placeholder="Start typing a message...",
    height=400,
)


with gr.Blocks(title="Ollama Chat") as demo:
    gr.HTML(
        """<div style='margin-top: 20px; margin-bottom: 20px'>
            <center>
                <h1>Ollama 对话测试</h1>
                <p>用于对 Ollama 本地大模型进行对话测试和参数调试</p>
            </center>
        </div>"""
    )

    with gr.Row():
        with gr.Column(scale=1):
            with gr.Group():
                base_url = gr.Textbox(
                    label="Base URL",
                    placeholder="http://127.0.0.1:11434",
                    value="http://127.0.0.1:11434",
                )
                model_dropdown = gr.Dropdown(choices=[], label="Models")

                fetch_models_button = gr.Button("Fetch Models")
                fetch_models_button.click(
                    fn=fetch_models, inputs=[base_url], outputs=model_dropdown
                )

            with gr.Group():
                max_tokens = gr.Slider(
                    label="Max Tokens", minimum=0, maximum=8192, value=4096, step=64
                )
                temperature = gr.Slider(
                    label="Temperature", minimum=0.0, maximum=5.0, value=0.3, step=0.1
                )
                top_k = gr.Slider(label="Top K", minimum=1, maximum=96, value=20)
                top_p = gr.Slider(
                    label="Top P", minimum=0.0, maximum=1.0, value=0.7, step=0.05
                )
                repeat_penalty = gr.Slider(
                    label="Repeat Penalty",
                    minimum=0.0,
                    maximum=10.0,
                    value=1.05,
                    step=0.05,
                )
                repeat_last_n = gr.Slider(
                    label="Repeat Last N", minimum=-1, maximum=8192, value=-1, step=1
                )
                seed = gr.Number(label="Seed", minimum=0, maximum=8192, value=0)

                with gr.Row():
                    copy_to_clip_button = gr.Button("Copy To Clipboard", size="sm")
                    copy_to_clip_button.click(fn=work_in_progress)
                    paste_from_clip_button = gr.Button(
                        "Paste From Clipboard", size="sm"
                    )
                    paste_from_clip_button.click(fn=work_in_progress)

                fetch_params_button = gr.Button("Load Params From Model")
                fetch_params_button.click(
                    fn=fetch_params,
                    inputs=[base_url, model_dropdown],
                    outputs=[
                        max_tokens,
                        temperature,
                        top_k,
                        top_p,
                        repeat_penalty,
                        repeat_last_n,
                    ],
                )

        with gr.Column(scale=3):
            system_prompt = gr.Textbox(
                label="System Prompt",
                placeholder="You are a helpful assistant.",
                value="You are a helpful assistant.",
                lines=5,
            )

            gr.ChatInterface(
                fn=do_chat,
                chatbot=chatbot,
                additional_inputs=[
                    base_url,
                    model_dropdown,
                    system_prompt,
                    temperature,
                    top_p,
                    max_tokens,
                    top_k,
                    repeat_penalty,
                    repeat_last_n,
                ],
            )


demo.launch(share=False)
