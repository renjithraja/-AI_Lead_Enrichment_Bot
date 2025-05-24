"""
Configuration settings for the Lead Enrichment Bot with Groq API
"""
import os
from typing import Dict, List

# API Configuration
GROQ_API_KEY = "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"  # Replace with your Groq API key
GEMINI_API_KEY = "AIzaSyBMSZXM6dCZnC3HblB6C35ezKo2K68YOIs"  # Fallback
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Groq API Settings
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama3-8b-8192"  # Fast and accurate model
# Alternative models: "llama3-70b-8192", "mixtral-8x7b-32768", "gemma2-9b-it"

# Gemini API Settings (fallback)
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
GEMINI_MODEL = "gemini-pro"

# Request Settings
REQUEST_TIMEOUT = 20
REQUEST_DELAY = 0.5  # Reduced delay for faster processing with Groq
MAX_RETRIES = 3

# Web Scraping Settings
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
MAX_CONTENT_LENGTH = 4000  # Increased for better context
MIN_CONTENT_LENGTH = 50    # Reduced minimum

# Common domain patterns for company website discovery
DOMAIN_PATTERNS = [
    "https://www.{company}.com",
    "https://{company}.com",
    "https://www.{company}.io",
    "https://{company}.io",
    "https://www.{company}.net",
    "https://{company}.net",
    "https://www.{company}.org",
    "https://{company}.org",
    "https://www.{company}.co",
    "https://{company}.co"
]

# Domains to skip during website discovery
SKIP_DOMAINS = [
    'facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com',
    'youtube.com', 'crunchbase.com', 'wikipedia.org', 'github.com',
    'reddit.com', 'medium.com', 'bloomberg.com', 'forbes.com',
    'bing.com', 'google.com', 'yahoo.com', 'pinterest.com'
]

# HTML elements to remove during scraping
REMOVE_ELEMENTS = ["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]

# Content selectors for extracting meaningful text
CONTENT_SELECTORS = [
    'main', '[role="main"]', '.main-content', '#main-content', '.content',
    '.hero', '.hero-section', '.banner', '.jumbotron',
    '.about', '.about-us', '.company', '.overview',
    '.description', '.intro', '.mission', '.vision',
    'article', 'section',
    'h1', 'h2', 'h3', 'p'
]

# Groq prompt template (optimized for Llama models)
GROQ_ANALYSIS_PROMPT = """You are a business intelligence expert. Analyze the company information below and provide insights.

Company: {company_name}
Website Content: {website_content}

Provide a JSON response with exactly these fields:
- "summary": 2-3 sentences describing what the company does, their main products/services
- "industry": Primary industry sector (e.g., Technology, Healthcare, Finance, Manufacturing)
- "automation_pitch": 2-3 sentences describing a specific AI automation solution for this company

Respond only with valid JSON, no additional text:"""

# Gemini prompt template (fallback)
GEMINI_ANALYSIS_PROMPT = """
Analyze the following company information:

Company Name: {company_name}
Website Content: {website_content}

Please provide:
1. A brief summary (2-3 sentences) of what this company does
2. The industry this company operates in (one or two words)
3. A custom AI automation idea that QF Innovate could pitch to this company (2-3 sentences focusing on their specific business needs)

Format your response as JSON:
{
    "summary": "Brief company summary here",
    "industry": "Industry name",
    "automation_pitch": "Custom AI automation pitch here"
}
"""

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'DEBUG',
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': 'enrichment_bot.log',
            'mode': 'a',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'file'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

# File paths
DEFAULT_INPUT_FILE = "input_companies.csv"
DEFAULT_OUTPUT_FILE = "enriched_companies.csv"
LOG_FILE = "enrichment_bot.log"

# Validation settings
REQUIRED_CSV_COLUMNS = ["company_name"]
OUTPUT_CSV_COLUMNS = [
    "company_name",
    "website", 
    "industry",
    "summary_from_llm",
    "automation_pitch_from_llm"
]