# summarize_module.py
import requests
import json
import re
import time


OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "llama3"
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds


def load_template(filepath: str = "CourseStructure.txt") -> str:
    """Load template file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def clean_json_string(json_str):
    """Clean common JSON formatting issues."""
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
    json_str = re.sub(r'^[^{]*', '', json_str)
    json_str = re.sub(r'[^}]*$', '', json_str)
    return json_str


def summarize_module(content: str, template: str, retry_count: int = 0) -> dict:
    """
    Summarize a module using Ollama with retry logic.
    Returns dict with 'summary' and 'success' keys.
    """
    prompt = (
        "You are an expert summarizer. Use the template structure below as your OUTPUT FORMAT. "
        "Fill in each section with actual content from the provided text. "
        "Keep the EXACT same headers, bullet points, numbering, and indentation as the template. "
        "Replace placeholder text with real summarized information from the content.\n\n"
        "CRITICAL: Respond ONLY with valid JSON. Do not include any notes, explanations, or text outside the JSON object. "
        "All property names must be in double quotes. Do not use trailing commas. "
        "Output must be a single JSON object in this format: {\"summary\": \"your formatted text here\"}.\n\n"
        f"TEMPLATE STRUCTURE (preserve this exact format):\n{template}\n\n"
        f"CONTENT TO SUMMARIZE:\n{content}\n\n"
        "Return ONLY: {\"summary\": \"...\"} where summary contains the filled template with preserved formatting."
    )
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "format": "json"
    }
    
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=120)
        json_lines = []
        
        for line in response.iter_lines():
            if line:
                response_obj = json.loads(line)
                if 'response' in response_obj:
                    json_lines.append(response_obj['response'])
        
        summary_str = ''.join(json_lines).strip()
        summary_str = clean_json_string(summary_str)
        
        try:
            summary_json = json.loads(summary_str)
        except Exception:
            try:
                import demjson3
                summary_json = demjson3.decode(summary_str)
            except Exception as e:
                raise Exception(f"JSON parsing failed: {e}")
        
        return {
            "summary": summary_json.get("summary", "[ERROR: No summary field in response]"),
            "success": True
        }
    
    except Exception as e:
        if retry_count < MAX_RETRIES:
            print(f"    ⚠️ Attempt {retry_count + 1} failed: {str(e)}")
            print(f"    Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
            return summarize_module(content, template, retry_count + 1)
        else:
            print(f"    ❌ Failed after {MAX_RETRIES} attempts: {str(e)}")
            return {
                "summary": f"[ERROR after {MAX_RETRIES} retries: {str(e)}]",
                "success": False
            }
