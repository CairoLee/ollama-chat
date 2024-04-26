import gradio as gr
from ollama import Client as ollama

def fetch_models(base_url):
    client = ollama(host=base_url)
    response = client.list()
    model_names = [model["name"] for model in response["models"]]
    return gr.update(choices=model_names, value=None if len(model_names) == 0 else model_names[0])
    

def predict(message, history, base_url, model_name, system_prompt, temperature, top_p, max_tokens, top_k, repeat_penalty, repeat_last_n):
    client = ollama(host=base_url)
    
    history_openai_format = []
    
    # 添加系统提示词
    if system_prompt is not None and system_prompt != "":
        history_openai_format.append({"role": "system", "content": system_prompt})
    
    # 添加历史对话
    for human, assistant in history:
        history_openai_format.append({"role": "user", "content": human })
        history_openai_format.append({"role": "assistant", "content": assistant})
    
    # 添加本次用户输入
    history_openai_format.append({"role": "user", "content": message})
  
    # 调用 ollama 的 SDK 接口进行对话
    response = client.chat(
        model=model_name,
        messages= history_openai_format,
        stream=True,
        options={
            'temperature': temperature,
            'num_ctx': max_tokens,
            'top_p': top_p,
            'top_k': top_k,
            'repeat_penalty': repeat_penalty,
            'repeat_last_n': repeat_last_n
        }
        )
    
    partial_message = ""
    for chunk in response:
        if chunk['message']['content'] is not None:
              partial_message = partial_message + chunk['message']['content']
              yield partial_message


chatbot = gr.Chatbot(
    placeholder="Start typing a message...",
    height=500,
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
            base_url = gr.Textbox(
                label="Base URL",
                placeholder="http://127.0.0.1:11434",
                value="http://127.0.0.1:11434"
                )
            system_prompt = gr.Textbox(
                label="System Prompt",
                placeholder="You are a helpful assistant.",
                value="You are a helpful assistant.",
                lines=5
                )
            max_tokens = gr.Slider(
                label="Max Tokens",
                minimum=0,
                maximum=8192,
                value=4096
                )
            temperature = gr.Slider(
                label="Temperature",
                minimum=0.0,
                maximum=5.0,
                value=0.3,
                step=0.1
                )
            top_k = gr.Slider(
                label="Top K",
                minimum=1,
                maximum=96,
                value=20
                )
            top_p = gr.Slider(
                label="Top P",
                minimum=0.0,
                maximum=1.0,
                value=0.7,
                step=0.05
                )
            repeat_penalty = gr.Slider(
                label="Repeat Penalty",
                minimum=0.0,
                maximum=10.0,
                value=1.05,
                step=0.05
                )
            repeat_last_n = gr.Slider(
                label="Repeat Last N",
                minimum=-1,
                maximum=8192,
                value=-1
                )
        with gr.Column(scale=2):
            with gr.Row():
                model_dropdown = gr.Dropdown(choices=[], label="Models", scale=2, value='qwen:1.8b')
                fetch_button = gr.Button("Fetch Models", scale=1)
            
            gr.ChatInterface(
                fn=predict,
                chatbot=chatbot,
                additional_inputs=[base_url, model_dropdown, system_prompt, temperature, top_p, max_tokens, top_k, repeat_penalty, repeat_last_n],
            )
        
            fetch_button.click(
                fn=fetch_models,
                inputs=[base_url],
                outputs=model_dropdown
            )


demo.launch(share=False)