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

def chunk_text(text: str, max_chars: int = 2000) -> List[str]:
    """Chunk content into manageable pieces."""
    return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

def build_prompt(template: str, chunk: str) -> str:
    return (
        "You are an expert summarizer. Use the following template as a guide for what topics and sections to cover in your summary. "
        "Create a comprehensive summary that addresses all the sections mentioned in the template. "
        "Respond ONLY with valid JSON in this exact format: {\"summary\": \"your summary text here\"}. "
        "No extra text, comments, or markdown. All property names must be in double quotes. "
        "The summary should be a clear, flowing narrative that covers all template sections.\n\n"
        f"TEMPLATE (use as guide for what to cover):\n{template}\n\n"
        f"CONTENT TO SUMMARIZE:\n{chunk}\n\n"
        "Return ONLY: {\"summary\": \"...\"}"
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

def ollama_summarize_simple(content: str, template: str) -> dict:
    chunks = chunk_text(content)
    all_summaries = []

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
        
        # Extract summary text if parsing succeeded
        if "summary" in summary_json:
            all_summaries.append(summary_json["summary"])
        elif "error" not in summary_json:
            # Fallback: try to get any text value
            all_summaries.append(str(summary_json))

    # Concatenate all chunk summaries into one
    final_summary = " ".join(all_summaries)
    
    return {
        "summary": final_summary
    }

# -- USAGE --
if __name__ == "__main__":
    template = load_file("CourseStructure.txt")  # Your template (guides what to cover)
    module_content = load_file("module1.txt")     # Content to summarize
    
    result = ollama_summarize_simple(module_content, template)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
