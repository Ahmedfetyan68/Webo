# main.py
from split_modules import load_file, split_learning_paths_and_modules
from summarize_module import summarize_module
import json

if __name__ == "__main__":
    # Load template and input file
    print("Loading files...")
    template = load_file("CourseStructure.txt")
    file_text = load_file("output.txt")
    
    # Split into learning paths and modules
    print("Splitting content into learning paths and modules...")
    path_map = split_learning_paths_and_modules(file_text)
    
    # Count total modules
    total_modules = sum(len(modules) for modules in path_map.values())
    print(f"Found {len(path_map)} learning paths with {total_modules} total modules.\n")
    
    # Summarize each module
    results = {}
    current_module = 0
    
    for path_name, modules in path_map.items():
        results[path_name] = {}
        
        for module_header, module_content in modules.items():
            current_module += 1
            print(f"[{current_module}/{total_modules}] Summarizing:")
            print(f"  Path: {path_name}")
            print(f"  Module: {module_header}")
            
            summary = summarize_module(module_content, template)
            results[path_name][module_header] = summary
            print(f"  ✓ Complete\n")
    
    # Save all summaries to a JSON file
    print("Saving all summaries to all_summaries.json...")
    with open("all_summaries.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("✓ All summaries saved successfully!")
    print(f"Processed {total_modules} modules across {len(path_map)} learning paths.")
