import requests
import json
import re
import demjson3
from typing import List

OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "llama3"

def load_file(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def chunk_text(text: str, max_chars: int = 1500) -> List[str]:
    return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

def build_prompt(template: str, chunk: str) -> str:
    return (
        "You are an expert assistant. Convert the following template sections into JSON keys. "
        "Use header text for keys; lists under headers become arrays. "
        "Respond ONLY with valid JSON. No extraneous text, comments, or markdown. "
        "All property names must be in double quotes. No trailing commas. "
        "TEMPLATE EXAMPLE:\n"
        f"{template}\n"
        "CONTENT:\n"
        f"{chunk}\n"
        "Return a strictly valid JSON object using these keys, with only JSON output."
    )

def fix_trailing_commas(json_str):
    return re.sub(r',(\s*[}\]])', r'\1', json_str)

def parse_json_robust(json_candidate):
    json_candidate = fix_trailing_commas(json_candidate)
    match = re.search(r'\{.*\}', json_candidate, flags=re.DOTALL)
    if match:
        json_candidate = match.group(0)
    try:
        return json.loads(json_candidate)
    except Exception:
        try:
            return demjson3.decode(json_candidate)
        except Exception:
            return {"error": "Could not parse JSON", "raw_output": json_candidate}

def ollama_summarize_with_template(content: str, template: str) -> dict:
    chunks = chunk_text(content)
    chunk_summaries = []

    for idx, chunk in enumerate(chunks):
        prompt = build_prompt(template, chunk)
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "format": "json"
        }

        response = requests.post(OLLAMA_API_URL, json=payload)
        json_lines = []
        for line in response.iter_lines():
            if line:
                response_obj = json.loads(line)
                if 'response' in response_obj:
                    json_lines.append(response_obj['response'])
        summary_str = ''.join(json_lines).strip()
        summary_json = parse_json_robust(summary_str)
        chunk_summaries.append(summary_json)

    if len(chunk_summaries) == 1:
        return chunk_summaries[0]
    else:
        return {
            "chunk_summaries": chunk_summaries,
            "note": "Content was chunked to fit model context window."
        }

# -- USAGE --
if __name__ == "__main__":
    template = load_file("CourseStructure.txt")  # Non-JSON template
    module_content = load_file("module1.txt")
    summary = ollama_summarize_with_template(module_content, template)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
