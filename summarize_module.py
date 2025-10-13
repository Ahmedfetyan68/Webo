# summarize_module.py
import requests
import json
import re

OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "llama3"

def clean_json_string(json_str):
    """Clean common JSON formatting issues."""
    # Remove trailing commas before } or ]
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
    # Remove any text before the first {
    json_str = re.sub(r'^[^{]*', '', json_str)
    # Remove any text after the last }
    json_str = re.sub(r'[^}]*$', '', json_str)
    return json_str

def summarize_module(content: str, template: str) -> str:
    """
    Summarize a module using Ollama and a template.
    Returns the summary as a string, or error message if parsing fails.
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
        
        # Clean the JSON string
        summary_str = clean_json_string(summary_str)
        
        # Try parsing with standard json
        try:
            summary_json = json.loads(summary_str)
        except Exception:
            # Fallback to demjson3 for tolerant parsing
            try:
                import demjson3
                summary_json = demjson3.decode(summary_str)
            except Exception as e:
                print(f"\n⚠️ Failed to parse JSON. Error: {e}")
                print(f"Raw output (first 500 chars):\n{summary_str[:500]}\n")
                return f"[ERROR: Could not parse JSON. Check logs for raw output.]"
        
        return summary_json.get("summary", "[ERROR: No summary field in response]")
    
    except Exception as e:
        print(f"\n⚠️ Error during summarization: {e}")
        return f"[ERROR: {str(e)}]"
