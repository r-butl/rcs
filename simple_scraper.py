#!/usr/bin/env python3
"""
Simple LinkedIn Job Scraper
"""

import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
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
    
    # Use the ChromeDriver we installed
    service = Service("/usr/local/bin/chromedriver")
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
    time.sleep(5)
    
    # Scroll to load all jobs
    for _ in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
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
        # Get job title
        title = ""
        title_selectors = [
            ".job-details-jobs-unified-top-card__job-title",
            "h1",
            "[data-test-id='job-details-job-title']"
        ]
        for selector in title_selectors:
            try:
                title = driver.find_element(By.CSS_SELECTOR, selector).text
                if title:
                    break
            except:
                continue
        
        # Get company name
        company = ""
        company_selectors = [
            ".job-details-jobs-unified-top-card__company-name",
            "[data-test-id='job-details-company-name']"
        ]
        for selector in company_selectors:
            try:
                company = driver.find_element(By.CSS_SELECTOR, selector).text
                if company:
                    break
            except:
                continue
        
        # Get description from the entire container
        description_html = ""
        description_text = ""
        container_selectors = [
            ".jobs-description__container",
            ".jobs-box--fadein.jobs-box--full-width.jobs-box--with-cta-large.jobs-description",
            ".job-details-module",
            ".jobs-box__html-content"
        ]
        for selector in container_selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                description_html = element.get_attribute("outerHTML")
                soup = BeautifulSoup(description_html, "html.parser")
                description_text = soup.get_text(separator="\n", strip=True)
                if description_text:
                    break
            except:
                continue
        
        # Summarize the description
        summarized_description = summarize_text(description_text, sentences=10)
        
        return {
            "title": title,
            "company": company,
            "description_text": summarized_description,
            "url": job_url
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
            print(f"Processing job {i}/{len(job_links)}")
            job_data = extract_job_data(driver, job_url)
            if job_data:
                jobs_data.append(job_data)
            time.sleep(2)
        
        # Save to file
        with open("saved_jobs.json", "w") as f:
            json.dump(jobs_data, f, indent=2)
        
        print(f"Saved {len(jobs_data)} jobs to saved_jobs.json")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
