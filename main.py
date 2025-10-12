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
        "You are an expert summarizer. Use the template structure below as your OUTPUT FORMAT. "
        "Fill in each section with actual content from the provided text. "
        "Keep the EXACT same headers, bullet points, numbering, and indentation as the template. "
        "Replace placeholder text with real summarized information from the content. "
        "Respond with ONLY valid JSON in this format: {\"summary\": \"your formatted text here\"}. "
        "The summary field must contain the filled template with all headers and formatting preserved.\n\n"
        f"TEMPLATE STRUCTURE (preserve this exact format):\n{template}\n\n"
        f"CONTENT TO SUMMARIZE:\n{chunk}\n\n"
        "Return ONLY: {\"summary\": \"...\"} where summary contains the filled template with preserved formatting."
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

def ollama_summarize_formatted(content: str, template: str) -> dict:
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

    # Concatenate all chunk summaries with double newline separation
    final_summary = "\n\n".join(all_summaries)
    
    return {
        "summary": final_summary
    }

# -- USAGE --
if __name__ == "__main__":
    template = load_file("CourseStructure.txt")  # Your template with structure
    module_content = load_file("module1.txt")     # Content to summarize
    
    result = ollama_summarize_formatted(module_content, template)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Optionally, save the formatted summary to a text file
    with open("formatted_summary.txt", "w", encoding="utf-8") as f:
        f.write(result["summary"])
    print("\nFormatted summary also saved to formatted_summary.txt")
