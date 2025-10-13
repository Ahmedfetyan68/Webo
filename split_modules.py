# split_modules.py
import re

def load_file(filepath: str) -> str:
    """Load and return text contents of a file with utf-8 encoding."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def split_learning_paths_and_modules(text):
    """
    Split text into learning paths, then modules within each path.
    Returns a nested dictionary: {path_name: {module_header: module_content}}
    """
    # Split by learning path headers
    path_splits = re.split(r'(=== Learning Path [^=]+ ===)', text)
    path_dict = {}
    
    for i in range(1, len(path_splits), 2):
        path_name = path_splits[i].strip('= \n').replace('\n', ' ')
        path_content = path_splits[i+1]
        
        # Split by module headers (robust pattern for various formats)
        modules = re.split(r'(---\s*Module\s*\d+\s*:.*?---)', path_content, flags=re.DOTALL)
        module_dict = {}
        
        for j in range(1, len(modules), 2):
            module_header = modules[j].strip('- \n').replace('\n', ' ')
            module_content = modules[j+1]
            module_dict[module_header] = module_content.strip()
        
        path_dict[path_name] = module_dict
    
    return path_dict
