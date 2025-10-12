import re

def load_file(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def split_learning_paths_and_modules(text):
    path_splits = re.split(r'(=== Learning Path [^=]+ ===)', text)
    path_dict = {}
    for i in range(1, len(path_splits), 2):
        path_name = path_splits[i].strip('= \n').replace('\n', ' ')
        path_content = path_splits[i+1]

        # Most robust: match any module header, even with dashes or special chars in the title
        modules = re.split(r'(---\s*Module\s*\d+\s*:.*?---)', path_content, flags=re.DOTALL)
        module_dict = {}
        for j in range(1, len(modules), 2):
            module_header = modules[j].strip('- \n').replace('\n', ' ')
            module_content = modules[j+1]
            module_dict[module_header] = module_content.strip()
        path_dict[path_name] = module_dict
    return path_dict

if __name__ == "__main__":
    file_text = load_file("paste.txt")
    path_map = split_learning_paths_and_modules(file_text)

    # Print all learning paths and all module headers for inspection
    for path in path_map:
        print(f"\nLEARNING PATH: {path}")
        for mod_title, mod_content in path_map[path].items():
            print(f"  MODULE: {mod_title}")
            print(f"    Sample: {mod_content[:200]}...\n")
        print("-" * 60)
