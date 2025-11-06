#!/usr/bin/env python3

import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import json
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer

def setup_driver():
    """Setup Chrome driver"""
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Automatically download and use the correct ChromeDriver version
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def summarize_text(text, sentences=10):
    """Summarize text using LexRank"""
    try:
        # Parse the text
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LexRankSummarizer()
        summary = summarizer(parser.document, sentences)
        summary_text = " ".join([str(sentence) for sentence in summary])
        
        return summary_text
    except Exception as e:
        print(f"Error summarizing text: {e}")
        # Return original text if summarization fails
        return text

def login_to_linkedin(driver, email, password):
    """Login to LinkedIn"""
    driver.get("https://www.linkedin.com/login")
    time.sleep(2)
    
    # Enter email
    email_field = driver.find_element(By.ID, "username")
    email_field.send_keys(email)
    
    # Enter password
    password_field = driver.find_element(By.ID, "password")
    password_field.send_keys(password)
    
    # Click login
    login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    login_button.click()
    time.sleep(5)

def get_saved_jobs(driver):
    """Get saved job links"""
    driver.get("https://www.linkedin.com/my-items/saved-jobs/")
    time.sleep(2)
    
    # Find job links - try multiple selectors
    selectors = [
        "a[href*='/jobs/view/']",
        "[data-test-id='job-card'] a",
        ".job-card-container a",
        "a[href*='linkedin.com/jobs/']"
    ]
    
    job_links = []
    for selector in selectors:
        try:
            links = driver.find_elements(By.CSS_SELECTOR, selector)
            for link in links:
                href = link.get_attribute("href")
                if href and "/jobs/view/" in href and href not in job_links:
                    job_links.append(href)
        except:
            continue
    
    return job_links

def extract_job_data(driver, job_url):
    """Extract job information"""
    driver.get(job_url)
    time.sleep(3)
    
    try:

        # Get description by finding "About the job" text and getting its parent container
        description_html = ""
        description_text = ""
        
        # Strategy 1: Find "About the job" text and get its parent container
        try:
            # Use XPath to find element containing "About the job" text (case-insensitive)
            about_job_element = driver.find_element(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'about the job')]")
            
            # Try to find a meaningful parent container (try up to 3 levels up)
            parent_element = None
            current_element = about_job_element
            
            # Try immediate parent first
            for level in range(3):
                try:
                    parent = current_element.find_element(By.XPATH, "..")
                    # Check if this parent has substantial content (more than just the heading)
                    parent_text = parent.text.strip()
                    if len(parent_text) > 500:  # If parent has substantial content, use it
                        parent_element = parent
                        break
                    current_element = parent
                except:
                    break
            
            # If we didn't find a good parent, use the immediate parent
            if parent_element is None:
                parent_element = about_job_element.find_element(By.XPATH, "..")
            
            # Get all text from the parent element
            description_html = parent_element.get_attribute("outerHTML")
            soup = BeautifulSoup(description_html, "html.parser")
            description_text = soup.get_text(separator="\n", strip=True)

            
        except Exception as e:
            print(f"Could not find 'About the job' element: {e}")
            pass
        
        return {
            "description_text": description_text,
            "url": job_url,
        }

    except Exception as e:
        print(f"Error extracting job data: {e}")
        return None


def main():
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment variables
    email = os.getenv('LINKEDIN_EMAIL')
    password = os.getenv('LINKEDIN_PASSWORD')
    
    if not email or not password:
        print("Error: Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in your .env file")
        print("Example .env file content:")
        print("LINKEDIN_EMAIL=your_email@example.com")
        print("LINKEDIN_PASSWORD=your_password_here")
        return
    
    driver = setup_driver()
    
    try:
        # Login
        login_to_linkedin(driver, email, password)
        
        # Get saved job links
        print("Getting saved job links...")
        job_links = get_saved_jobs(driver)
        print(f"Found {len(job_links)} saved jobs")
        
        # Extract data from each job
        jobs_data = []
        for i, job_url in enumerate(job_links, 1):
            print(f"\n{'#'*80}")
            print(f"Processing job {i}/{len(job_links)}: {job_url}")
            print(f"{'#'*80}")
            job_data = extract_job_data(driver, job_url)
            if job_data:
                print(f"✓ Successfully extracted: {job_data.get('title', 'N/A')} at {job_data.get('company', 'N/A')}")
                jobs_data.append(job_data)
            else:
                print(f"✗ Failed to extract job data")
            time.sleep(2)
        
        # Save to file
        with open("saved_jobs.json", "w") as f:
            json.dump(jobs_data, f, indent=2)
        
        print(f"Saved {len(jobs_data)} jobs to saved_jobs.json")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
