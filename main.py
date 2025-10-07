import requests
import json
from typing import List

OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "llama2"  # Use your preferred model; make sure it is pulled via ollama CLI

def load_file(filepath: str) -> str:
    """Load and return the text contents of a file with utf-8 encoding."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def chunk_text(text: str, max_chars: int = 3000) -> List[str]:
    """Simple chunking for long text based on characters (conservative)."""
    return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

def prompt_from_template(template: str, chunk: str) -> str:
    """Assemble the prompt string to guide the model for JSON output."""
    return (
        "You are an expert summarizer. "
        "Given the template below, create a summary of the provided content as **valid JSON**. "
        "Each header in the template must be used as a JSON key, and lists must be arrays. "
        "Output ONLY valid JSON with all keys present.\n\n"
        "TEMPLATE:\n"
        f"{template}\n\n"
        "CONTENT TO SUMMARIZE:\n"
        f"{chunk}"
    )

def ollama_summarize_with_template(content: str, template: str) -> dict:
    """Summarize the chunked content via Ollama, enforcing JSON output matching template."""
    chunks = chunk_text(content)
    chunk_summaries = []

    for idx, chunk in enumerate(chunks):
        prompt = prompt_from_template(template, chunk)
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt
        }

        response = requests.post(OLLAMA_API_URL, json=payload)
        json_lines = []
        for line in response.iter_lines():
            if line:
                response_obj = json.loads(line)
                if 'response' in response_obj:
                    json_lines.append(response_obj['response'])
        summary_str = ''.join(json_lines).strip()
        # Attempt to parse summarization as JSON
        try:
            summary_json = json.loads(summary_str)
        except json.JSONDecodeError:
            summary_json = {
                "error": "Invalid JSON returned by model",
                "raw_output": summary_str
            }
        chunk_summaries.append(summary_json)

    if len(chunk_summaries) == 1:
        return chunk_summaries[0]
    else:
        return {
            "chunk_summaries": chunk_summaries,
            "note": "Content was chunked to fit model context window."
        }

# ---- USAGE EXAMPLE ----

if __name__ == "__main__":
    # Load the template from file
    template = load_file("CourseStructure.txt")
    # Load your module content from another file
    module_content = load_file("module1.txt")  # Replace as needed

    # Run summarization
    summary = ollama_summarize_with_template(module_content, template)
    # Print or store the summary as a JSON object
    print(json.dumps(summary, indent=2, ensure_ascii=False))
