from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import google.generativeai as genai
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin

# -------- GEMINI SETUP ---------
genai.configure(api_key="AIzaSyDgORyXsBcfO5Y8QYZZ2rYmaKQ0JA6n6Bw")  # Set your real key here
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

with open("CourseStructure.txt", "r", encoding="utf-8") as f:
    COURSE_STRUCTURE = f.read()

# -------- FASTAPI SETUP ---------
class CourseRequest(BaseModel):
    learn_url: str

app = FastAPI()

# -------- SCRAPER FUNCTIONS ---------
def get_learning_paths(course_url):
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
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=60000)
            page.wait_for_selector("h1", timeout=8000)
            title_elem = page.query_selector("h1")
            title = title_elem.inner_text().strip() if title_elem else "No Title Found"
            content_elem = page.query_selector("main") or page.query_selector("body")
            content = content_elem.inner_text().strip() if content_elem else ""
        except Exception as e:
            title = f"Error loading page: {url}"
            content = str(e)
        browser.close()
    return title, content

def summarize_with_gemini(content: str, template: str) -> str:
    prompt = f"""You are a helpful assistant. I will give you raw content from a Microsoft Learn training module.
Summarize it using the same format as the example below.

---
Example Summary:
{template}

---
Module Content:
{content}
"""
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"[Gemini Error] {e}"

# --------- API ENDPOINT ---------
@app.post("/summarize-learn-course")
def summarize_learn_course(req: CourseRequest):
    learning_paths = get_learning_paths(req.learn_url)
    if not learning_paths:
        return {"error": "No learning paths found for this course link."}

    summaries = []
    for path in learning_paths:
        modules = get_inner_modules(path["url"])
        for mod in modules:
            title, content = scrape_module_content(mod['url'])
            summary = summarize_with_gemini(content, COURSE_STRUCTURE)
            summaries.append({
                "module_title": title,
                "module_url": mod['url'],
                "summary": summary
            })
    return {"course_url": req.learn_url, "summaries": summaries}

# ------ Run with: uvicorn filename:app --host 0.0.0.0 --port 8000 --------
