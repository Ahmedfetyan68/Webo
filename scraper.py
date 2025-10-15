# scraper.py
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin
import json
import re


def get_course_overview(course_url):
    """Extract course overview from the main course page."""
    overview_text = ""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(course_url, wait_until='networkidle', timeout=60000)
        
        page.wait_for_timeout(3000)
        
        all_headings = page.query_selector_all("h2")
        
        for heading in all_headings:
            heading_text = heading.inner_text().strip()
            if heading_text.lower() == "overview":
                next_element = heading.evaluate_handle("el => el.nextElementSibling")
                
                if next_element:
                    tag_name = next_element.evaluate("el => el.tagName.toLowerCase()")
                    
                    if tag_name == "p":
                        overview_text = next_element.inner_text().strip()
                    elif tag_name == "div":
                        first_p = next_element.query_selector("p")
                        if first_p:
                            overview_text = first_p.inner_text().strip()
                break
        
        browser.close()
    return overview_text


def get_learning_path_time(path_url):
    """Extract time estimate from a learning path page."""
    time_text = ""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(path_url, wait_until='networkidle', timeout=60000)
        
        page.wait_for_timeout(3000)
        
        time_elem = page.query_selector("li#time-remaining")
        
        if time_elem:
            time_text = time_elem.inner_text().strip()
        else:
            time_elem = page.query_selector("li.module-duration-minutes")
            if time_elem:
                time_text = time_elem.inner_text().strip()
            else:
                metadata_ul = page.query_selector("ul.metadata")
                if metadata_ul:
                    list_items = metadata_ul.query_selector_all("li")
                    for li in list_items:
                        text = li.inner_text().strip()
                        if re.search(r'\d+\s*(hr|min)', text, re.IGNORECASE) and len(text) < 30:
                            time_text = text
                            break
                
                if not time_text:
                    all_list_items = page.query_selector_all("li")
                    for li in all_list_items:
                        text = li.inner_text().strip()
                        if re.search(r'\d+\s*(hr|min)', text, re.IGNORECASE) and len(text) < 30:
                            if not re.search(r'[a-zA-Z]{10,}', text):
                                time_text = text
                                break
        
        browser.close()
    return time_text


def get_learning_paths(course_url):
    """Get all learning paths from the course page."""
    learning_paths = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(course_url, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(3000)

        anchors = page.query_selector_all("a.card-title")
        for a in anchors:
            href = a.get_attribute("href") or ""
            text = (a.inner_text() or "").strip()
            if "/training/paths/" in href:
                full_url = urljoin(course_url, href)
                learning_paths.append({"url": full_url, "title": text})

        browser.close()
    return learning_paths


def get_inner_modules(path_url):
    """Get all modules from a learning path page."""
    module_links = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(path_url, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(2000)

        anchors = page.query_selector_all("a.unit-title, a.module-title")
        if not anchors:
            anchors = [
                a for a in page.query_selector_all("a[data-linktype='relative-path']")
                if "/training/modules/" in (a.get_attribute("href") or "")
            ]

        for a in anchors:
            href = a.get_attribute("href") or ""
            text = (a.inner_text() or "").strip()
            if "/training/modules/" in href:
                full_url = urljoin(path_url, href)
                module_links.append({"url": full_url, "title": text})

        browser.close()
    return module_links


def scrape_module_content(url):
    """Scrape full content from a module page."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=60000)
            page.wait_for_selector("h1", timeout=8000)

            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(3000)

            title_elem = page.query_selector("h1")
            title = title_elem.inner_text().strip() if title_elem else "No Title Found"

            content_elem = page.query_selector("main") or page.query_selector("body")

            if content_elem:
                paragraphs = content_elem.query_selector_all("p")
                content = "\n\n".join(p.inner_text().strip() for p in paragraphs if p.inner_text().strip())
            else:
                content = ""

        except Exception as e:
            title = f"Error loading page: {url}"
            content = str(e)
        finally:
            browser.close()
    return title, content


def scrape_full_course(course_url):
    """
    Main scraping function that coordinates all scraping operations.
    Returns complete course data structure.
    """
    print("Scraping course overview...")
    overview = get_course_overview(course_url)
    print("✓ Overview extracted\n")

    print("Getting learning paths...")
    learning_paths = get_learning_paths(course_url)
    print(f"✓ Found {len(learning_paths)} learning paths\n")

    all_data = {
        "course_url": course_url,
        "overview": overview,
        "learning_paths": []
    }

    for path_index, path in enumerate(learning_paths, 1):
        print(f"[{path_index}/{len(learning_paths)}] Processing path: {path['title']}")
        
        time_estimate = get_learning_path_time(path["url"])
        print(f"  Time estimate: {time_estimate}")
        
        modules = get_inner_modules(path["url"])
        print(f"  Found {len(modules)} modules")

        path_data = {
            "path_title": path["title"],
            "path_url": path["url"],
            "time_estimate": time_estimate,
            "modules": []
        }

        for mod_index, mod in enumerate(modules, 1):
            print(f"    [{mod_index}/{len(modules)}] Scraping: {mod['title']}")
            title, content = scrape_module_content(mod['url'])
            path_data["modules"].append({
                "module_title": title,
                "module_url": mod['url'],
                "content": content
            })

        all_data["learning_paths"].append(path_data)
        print()

    return all_data
