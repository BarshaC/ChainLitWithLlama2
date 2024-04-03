import chainlit as cl
import requests
import os
import json
import asyncio

version_id = os.environ["VERSION_ID"]
baseten_api_key = os.environ["BASETEN_API_KEY"]
model_id = os.environ['MODEL_ID']  # Update with your model ID

async def display_message(message: cl.Message, content: str, delay: float):
    words = content.split()
    for word in words:
        message.content += word + " "
        await message.update()
        await asyncio.sleep(delay)

@cl.on_message
async def main(message: cl.Message):
    # First request to Basenet API using the user's input message content
    resp = requests.post(
        f"https://model-{model_id}.api.baseten.co/production/predict",
        headers={"Authorization": f"Api-Key {baseten_api_key}"},
        json={'top_p': 0.75, 'prompt': message.content, 'num_beams': 4, 'temperature': 0.1},
    )
    resp_json = resp.json()
    
    # Extracting the response text from the JSON response
    resp_text = resp_json[0]
    
    # Display the response from the first request within ChainLit
    ui_msg_first_resp = cl.Message(
        author="Llama 2",
        content="",
    )
    await ui_msg_first_resp.send()
    await display_message(ui_msg_first_resp, resp_text, delay=0.1)  # Adjust delay as needed
    
    # ChainLit response setup
    prompt_history = cl.user_session.get("prompt_history", "")
    prompt = f"{prompt_history}{message.content}"
    response = ""

    ui_msg = cl.Message(
        author="Llama 2",
        content="",
    )

    # Second request to Basenet API
    s = requests.Session()
    with s.post(
        f"https://app.baseten.co/model_versions/{version_id}/predict",
        headers={"Authorization": f"Api-Key {baseten_api_key}"},
        data=json.dumps({"prompt": prompt, "stream": True, "max_new_tokens": 4096}),
        stream=True,
    ) as resp:
        buffer = ""
        start_response = False
        for token in resp.iter_content(1):
            token = token.decode("utf-8")
            buffer += token
            if not start_response:
                if "[/INST]" in buffer:
                    start_response = True
            else:
                response += token
                await ui_msg.stream_token(token)

    await ui_msg.send()
    
    # Update prompt history
    prompt_history += message.content + response
    cl.user_session.set("prompt_history", prompt_history)
