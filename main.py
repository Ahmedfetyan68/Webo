# main.py
from scraper import scrape_full_course
from summarize_module import summarize_module, load_template
import json
from datetime import datetime


def save_intermediate_results(data, filename="intermediate_summaries.json"):
    """Save intermediate results to prevent data loss."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    COURSE_URL = "https://learn.microsoft.com/en-us/training/courses/pl-200t00"
    
    # Step 1: Scrape the course
    print("="*80)
    print("STEP 1: SCRAPING COURSE DATA")
    print("="*80)
    scraped_data = scrape_full_course(COURSE_URL)
    
    # Save scraped data
    with open("scraped_course.json", "w", encoding="utf-8") as f:
        json.dump(scraped_data, f, indent=2, ensure_ascii=False)
    print("✓ Scraped data saved to scraped_course.json\n")
    
    # Step 2: Load template
    print("="*80)
    print("STEP 2: LOADING TEMPLATE")
    print("="*80)
    template = load_template("CourseStructure.txt")
    print("✓ Template loaded\n")
    
    # Step 3: Summarize modules
    print("="*80)
    print("STEP 3: SUMMARIZING MODULES")
    print("="*80)
    
    # Count total modules
    total_modules = sum(len(path["modules"]) for path in scraped_data["learning_paths"])
    print(f"Total modules to process: {total_modules}\n")
    
    # Build results structure (same as scraped but with summaries instead of content)
    results = {
        "course_url": scraped_data["course_url"],
        "overview": scraped_data["overview"],
        "learning_paths": []
    }
    
    current_module = 0
    failed_modules = []
    
    for path in scraped_data["learning_paths"]:
        path_result = {
            "path_title": path["path_title"],
            "path_url": path["path_url"],
            "time_estimate": path["time_estimate"],
            "modules": []
        }
        
        for module in path["modules"]:
            current_module += 1
            print(f"[{current_module}/{total_modules}] Summarizing:")
            print(f"  Path: {path['path_title']}")
            print(f"  Module: {module['module_title']}")
            
            # Summarize with retry logic
            result = summarize_module(module["content"], template)
            
            module_result = {
                "module_title": module["module_title"],
                "module_url": module["module_url"],
                "summary": result["summary"]
            }
            
            if not result["success"]:
                failed_modules.append({
                    "path": path["path_title"],
                    "module": module["module_title"],
                    "url": module["module_url"]
                })
            
            path_result["modules"].append(module_result)
            print(f"  ✓ Complete\n")
            
            # Save intermediate results every 5 modules
            if current_module % 5 == 0:
                temp_results = results.copy()
                temp_results["learning_paths"].append(path_result)
                save_intermediate_results(temp_results)
                print(f"  💾 Intermediate save (after {current_module} modules)\n")
        
        results["learning_paths"].append(path_result)
    
    # Step 4: Save final results
    print("="*80)
    print("STEP 4: SAVING FINAL RESULTS")
    print("="*80)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = "all_summaries.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"✓ All summaries saved to {output_file}")
    print(f"✓ Processed {total_modules} modules across {len(results['learning_paths'])} learning paths")
    
    if failed_modules:
        print(f"\n⚠️ {len(failed_modules)} module(s) failed summarization:")
        for fail in failed_modules:
            print(f"  - {fail['path']} > {fail['module']}")
    else:
        print("\n✅ All modules summarized successfully!")
    
    print("="*80)
