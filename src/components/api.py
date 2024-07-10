import json
import openai
import os
from anthropic import Anthropic

def setup_openai_api(api_key):
    openai.api_key = api_key

def setup_claude_api(api_key):
    os.environ['ANTHROPIC_API_KEY'] = api_key
    global client
    client = Anthropic(api_key=api_key)

def save_api_keys(api_keys):
    with open("api_keys.json", "w") as file:
        json.dump(api_keys, file)

def load_api_keys():
    if os.path.exists("api_keys.json"):
        with open("api_keys.json", "r") as file:
            return json.load(file)
    return {}

def handle_api_error(e):
    print(f"API Error: {e}")
    
def get_code_suggestions(messages, system_prompt=None):
    try:
        print(f"Sending request to OpenAI API with messages: {messages}")
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=4096
        )
        print(f"Received response from OpenAI API: {response}")

        return response.choices[0].message['content'].strip()

    except Exception as e:
        handle_api_error(e)
        return ""

def read_file_content(file_path):
    try:
        with open(file_path, "r") as file:
            return file.read().strip()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def read_system_prompt(file_name="system_prompt.txt"):
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Directory where IDE.py is located
    file_path = os.path.join(script_dir, file_name)
    return read_file_content(file_path)
