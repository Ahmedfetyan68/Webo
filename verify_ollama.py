import requests
import json

OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"

payload = {
    "model": "llama2",  # Replace with your model
    "prompt": "Say hello!"
}

response = requests.post(OLLAMA_API_URL, json=payload)
for line in response.iter_lines():
    if line:
        chunk = json.loads(line)
        print(chunk)
