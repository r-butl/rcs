#!/usr/bin/env python3
"""
Test script to summarize job descriptions from saved_jobs.json using sumy
"""

import nltk
nltk.download('punkt_tab')

import json
import os
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from sumy.summarizers.luhn import LuhnSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words

def load_jobs_data(filename="saved_jobs.json"):
    """Load jobs data from JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {filename} not found")
        return []
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {filename}")
        return []

def clean_text(text):
    """Clean and prepare text for summarization"""
    if not text:
        return ""
    
    # Remove extra whitespace and normalize
    text = ' '.join(text.split())
    return text

def summarize_text(text, sentences_count=10, method='lsa'):
    """Summarize text using different methods"""
    if not text or len(text.split()) < 50:  # Skip very short texts
        return "Text too short to summarize effectively."
    
    try:
        # Initialize parser and tokenizer
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        stemmer = Stemmer("english")
        
        # Choose summarizer method
        if method == 'lsa':
            summarizer = LsaSummarizer(stemmer)
        elif method == 'lexrank':
            summarizer = LexRankSummarizer(stemmer)
        elif method == 'luhn':
            summarizer = LuhnSummarizer(stemmer)
        else:
            summarizer = LsaSummarizer(stemmer)
        
        # Set stop words
        summarizer.stop_words = get_stop_words("english")
        
        # Generate summary
        summary_sentences = summarizer(parser.document, sentences_count)
        summary = ' '.join([str(sentence) for sentence in summary_sentences])
        
        return summary
    
    except Exception as e:
        return f"Error summarizing text: {str(e)}"

def main():
    """Main function to test job summarization"""
    print("Loading saved jobs data...")
    jobs = load_jobs_data()
    
    if not jobs:
        print("No jobs data found. Please run the scraper first.")
        return
    
    print(f"Found {len(jobs)} jobs to summarize\n")
    
    # Test different summarization methods
    methods = ['lsa', 'lexrank', 'luhn']
    
    for i, job in enumerate(jobs[:3], 1):  # Test first 3 jobs
        print(f"=== JOB {i}: {job.get('title', 'Unknown Title')} ===")
        print(f"Company: {job.get('company', 'Unknown Company')}")
        print(f"URL: {job.get('url', 'No URL')}")
        print()
        
        description = job.get('description_text', '')
        if not description:
            description = job.get('description', '')
        
        cleaned_text = clean_text(description)
        
        if cleaned_text:
            print(f"Original text length: {len(cleaned_text)} characters")
            print(f"Word count: {len(cleaned_text.split())}")
            print()
            
            # Test each summarization method
            for method in methods:
                print(f"--- {method.upper()} Summary (10 sentences) ---")
                summary = summarize_text(cleaned_text, sentences_count=5, method=method)
                print(summary)
                print(f"Summary length: {len(summary)} characters")
                print()
        else:
            print("No description text found for this job.")
        
        print("=" * 80)
        print()

if __name__ == "__main__":
    main()
