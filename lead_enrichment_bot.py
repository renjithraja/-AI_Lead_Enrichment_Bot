import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import json
import re
from urllib.parse import urljoin, urlparse
import logging
from typing import Dict, List, Optional
import os
from dataclasses import dataclass
from config import *  # Import all configuration settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CompanyData:
    name: str
    website: str = ""
    industry: str = ""
    company_size: str = ""
    hq_location: str = ""
    summary: str = ""
    automation_pitch: str = ""

class LeadEnrichmentBot:
    def __init__(self, groq_api_key: str = None, gemini_api_key: str = None):
        # API Keys
        self.groq_api_key = groq_api_key or GROQ_API_KEY
        self.gemini_api_key = gemini_api_key or GEMINI_API_KEY
        
        # Session for web requests
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        
        # Validate API keys
        if not self.groq_api_key or self.groq_api_key == "your_groq_api_key_here":
            logger.warning("No valid Groq API key provided, will use Gemini as fallback")
            if not self.gemini_api_key:
                logger.error("No valid API keys provided!")
        
    def search_company_website(self, company_name: str) -> str:
        """Search for company website using multiple strategies"""
        logger.info(f"Searching website for: {company_name}")
        
        try:
            # Strategy 1: Try common domain patterns
            website = self._try_common_domains(company_name)
            if website:
                logger.info(f"Found via common domains: {website}")
                return website
            
            # Strategy 2: Use web search
            website = self._search_via_web(company_name)
            if website:
                logger.info(f"Found via web search: {website}")
                return website
            
            logger.warning(f"Could not find website for {company_name}")
            return ""
            
        except Exception as e:
            logger.error(f"Error finding website for {company_name}: {e}")
            return ""
    
    def _try_common_domains(self, company_name: str) -> str:
        """Try common domain patterns"""
        # Clean company name for domain testing
        clean_name_variations = [
            re.sub(r'[^a-zA-Z0-9]', '', company_name.lower()),
            company_name.lower().replace(' ', '').replace('.', '').replace(',', ''),
            company_name.lower().split()[0] if ' ' in company_name else company_name.lower(),
        ]
        
        # Remove duplicates while preserving order
        clean_names = list(dict.fromkeys(clean_name_variations))
        
        for clean_name in clean_names:
            if len(clean_name) < 2:  # Skip very short names
                continue
                
            potential_domains = [
                f"https://www.{clean_name}.com",
                f"https://{clean_name}.com",
                f"https://www.{clean_name}.io",
                f"https://{clean_name}.io",
                f"https://www.{clean_name}.co",
                f"https://{clean_name}.co",
                f"https://www.{clean_name}.net",
                f"https://{clean_name}.net",
                f"https://www.{clean_name}.org",
                f"https://{clean_name}.org"
            ]
            
            for domain in potential_domains:
                try:
                    response = self.session.get(domain, timeout=REQUEST_TIMEOUT, allow_redirects=True)
                    if response.status_code == 200 and len(response.content) > 1000:
                        # Check if it's not a parked domain
                        content = response.text.lower()
                        parked_indicators = ['domain for sale', 'parked domain', 'buy this domain', 'domain expired']
                        if not any(indicator in content for indicator in parked_indicators):
                            return domain
                except Exception as e:
                    logger.debug(f"Domain {domain} failed: {e}")
                    continue
        
        return ""
    
    def _search_via_web(self, company_name: str) -> str:
        """Search for company website using web search"""
        try:
            # Use DuckDuckGo search (no API key required)
            search_query = f"{company_name} official website"
            search_url = f"https://duckduckgo.com/html/?q={requests.utils.quote(search_query)}"
            
            response = self.session.get(search_url, timeout=REQUEST_TIMEOUT)
            if response.status_code != 200:
                return ""
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for search results
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if 'uddg=' in href:
                    try:
                        # Extract actual URL from DuckDuckGo redirect
                        actual_url = requests.utils.unquote(href.split('uddg=')[1])
                        if self._is_likely_company_website(actual_url, company_name):
                            return actual_url
                    except:
                        continue
            
            return ""
        except Exception as e:
            logger.error(f"Web search failed for {company_name}: {e}")
            return ""
    
    def _is_likely_company_website(self, url: str, company_name: str) -> bool:
        """Check if URL is likely the company's official website"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Skip unwanted domains
            if any(skip_domain in domain for skip_domain in SKIP_DOMAINS):
                return False
            
            # Check if company name parts are in domain
            company_words = re.findall(r'\w+', company_name.lower())
            domain_clean = re.sub(r'[^a-zA-Z0-9]', '', domain)
            
            # If any significant word from company name is in domain
            for word in company_words:
                if len(word) > 3 and word in domain_clean:
                    return True
            
            return False
        except:
            return False
    
    def scrape_website_content(self, url: str) -> str:
        """Scrape and extract meaningful content from website"""
        try:
            logger.info(f"Scraping content from: {url}")
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(REMOVE_ELEMENTS):
                element.decompose()
            
            # Extract content from specific areas
            content_areas = []
            
            # Try content selectors in order of priority
            for selector in CONTENT_SELECTORS:
                try:
                    elements = soup.select(selector)
                    for element in elements:
                        text = element.get_text(strip=True)
                        if len(text) > MIN_CONTENT_LENGTH:
                            content_areas.append(text)
                except:
                    continue
            
            # Combine and clean content
            full_text = ' '.join(content_areas)
            full_text = re.sub(r'\s+', ' ', full_text).strip()
            
            # Limit content length
            content = full_text[:MAX_CONTENT_LENGTH] if full_text else ""
            logger.info(f"Scraped {len(content)} characters of content")
            
            return content
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return ""
    
    def analyze_with_groq(self, company_name: str, website_content: str) -> Dict[str, str]:
        """Use Groq API to analyze company and generate insights"""
        if not self.groq_api_key or self.groq_api_key == "your_groq_api_key_here":
            return {"summary": "", "automation_pitch": "", "industry": ""}
        
        try:
            logger.info(f"Analyzing {company_name} with Groq AI...")
            
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = GROQ_ANALYSIS_PROMPT.format(
                company_name=company_name,
                website_content=website_content[:3000]  # Limit content for API
            )
            
            payload = {
                "model": GROQ_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a business intelligence expert who provides accurate, structured analysis of companies. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 1000,
                "top_p": 1,
                "stream": False
            }
            
            response = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Groq API response received for {company_name}")
            
            if 'choices' in result and result['choices']:
                content = result['choices'][0]['message']['content'].strip()
                logger.info(f"Raw Groq response: {content[:200]}...")
                
                # Parse JSON response
                try:
                    # Clean the response
                    content = content.replace('```json', '').replace('```', '').strip()
                    
                    # Find and parse JSON
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                        json_data = json.loads(json_str)
                        
                        result_data = {
                            "summary": json_data.get("summary", "").strip(),
                            "industry": json_data.get("industry", "").strip(),
                            "automation_pitch": json_data.get("automation_pitch", "").strip()
                        }
                        
                        logger.info(f"Successfully parsed Groq response for {company_name}")
                        return result_data
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parsing failed for {company_name}, trying fallback: {e}")
                    return self._parse_text_response(content)
            
            logger.warning(f"No valid response from Groq for {company_name}")
            return {"summary": "", "automation_pitch": "", "industry": ""}
            
        except Exception as e:
            logger.error(f"Groq API error for {company_name}: {e}")
            return {"summary": "", "automation_pitch": "", "industry": ""}
    
    def analyze_with_gemini(self, company_name: str, website_content: str) -> Dict[str, str]:
        """Use Gemini API as fallback"""
        if not self.gemini_api_key:
            return {"summary": "", "automation_pitch": "", "industry": ""}
        
        try:
            logger.info(f"Analyzing {company_name} with Gemini AI (fallback)...")
            
            url = f"{GEMINI_API_URL}?key={self.gemini_api_key}"
            
            prompt = GEMINI_ANALYSIS_PROMPT.format(
                company_name=company_name,
                website_content=website_content[:2000]
            )
            
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 1000
                }
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if 'candidates' in result and result['candidates']:
                content = result['candidates'][0]['parts'][0]['text'].strip()
                
                # Try to parse JSON
                try:
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        json_data = json.loads(json_match.group())
                        return {
                            "summary": json_data.get("summary", "").strip(),
                            "industry": json_data.get("industry", "").strip(),
                            "automation_pitch": json_data.get("automation_pitch", "").strip()
                        }
                except json.JSONDecodeError:
                    pass
                
                return self._parse_text_response(content)
            
            return {"summary": "", "automation_pitch": "", "industry": ""}
            
        except Exception as e:
            logger.error(f"Gemini API error for {company_name}: {e}")
            return {"summary": "", "automation_pitch": "", "industry": ""}
    
    def _parse_text_response(self, content: str) -> Dict[str, str]:
        """Parse text response when JSON parsing fails"""
        logger.info("Using fallback text parsing")
        
        result = {"summary": "", "industry": "", "automation_pitch": ""}
        
        try:
            lines = content.split('\n')
            current_key = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for key indicators
                if any(word in line.lower() for word in ['summary', 'about', 'description']):
                    current_key = 'summary'
                    if ':' in line:
                        result['summary'] = line.split(':', 1)[1].strip()
                elif any(word in line.lower() for word in ['industry', 'sector', 'business']):
                    current_key = 'industry'
                    if ':' in line:
                        result['industry'] = line.split(':', 1)[1].strip()
                elif any(word in line.lower() for word in ['automation', 'pitch', 'solution']):
                    current_key = 'automation_pitch'
                    if ':' in line:
                        result['automation_pitch'] = line.split(':', 1)[1].strip()
                elif current_key and len(line) > 10:
                    if result[current_key]:
                        result[current_key] += " " + line
                    else:
                        result[current_key] = line
            
            # Clean up results
            for key in result:
                result[key] = result[key][:500]  # Limit length
                
        except Exception as e:
            logger.error(f"Fallback parsing failed: {e}")
        
        return result
    
    def enrich_company(self, company_name: str) -> CompanyData:
        """Enrich a single company with all available data"""
        logger.info(f"=== Starting enrichment for: {company_name} ===")
        
        # Initialize company data
        company = CompanyData(name=company_name)
        
        try:
            # Step 1: Find website
            logger.info("Step 1: Finding website...")
            company.website = self.search_company_website(company_name)
            
            if not company.website:
                logger.warning(f"No website found for {company_name}")
                # Try to get basic info from AI without website content
                analysis = self.analyze_with_groq(company_name, f"Company name: {company_name}")
                if not analysis or not analysis.get("summary"):
                    analysis = self.analyze_with_gemini(company_name, f"Company name: {company_name}")
                
                company.summary = analysis.get("summary", f"Company information for {company_name} not available")
                company.industry = analysis.get("industry", "Unknown")
                company.automation_pitch = analysis.get("automation_pitch", "Contact QF Innovate for custom AI automation solutions")
                return company
            
            logger.info(f"✅ Website found: {company.website}")
            
            # Step 2: Scrape website content
            logger.info("Step 2: Scraping website content...")
            website_content = self.scrape_website_content(company.website)
            
            if not website_content:
                logger.warning(f"No content scraped from {company.website}")
                website_content = f"Company website: {company.website}"
            else:
                logger.info(f"✅ Content scraped: {len(website_content)} characters")
            
            # Step 3: Analyze with AI (try Groq first, then Gemini)
            logger.info("Step 3: Analyzing with AI...")
            analysis = self.analyze_with_groq(company_name, website_content)
            
            # If Groq fails or returns empty results, try Gemini
            if not analysis or not analysis.get("summary"):
                logger.info("Groq analysis failed, trying Gemini...")
                analysis = self.analyze_with_gemini(company_name, website_content)
            
            company.summary = analysis.get("summary", "")
            company.industry = analysis.get("industry", "")
            company.automation_pitch = analysis.get("automation_pitch", "")
            
            logger.info(f"✅ Analysis complete for {company_name}")
            logger.info(f"   Summary: {company.summary[:100]}...")
            logger.info(f"   Industry: {company.industry}")
            logger.info(f"   Pitch: {company.automation_pitch[:100]}...")
            
        except Exception as e:
            logger.error(f"Error during enrichment of {company_name}: {e}")
            company.summary = f"Error during processing: {str(e)}"
        
        # Add delay to be respectful to APIs
        time.sleep(REQUEST_DELAY)
        
        logger.info(f"=== Completed enrichment for: {company_name} ===\n")
        return company
    
    def process_csv(self, input_csv_path: str, output_csv_path: str) -> pd.DataFrame:
        """Process the entire CSV file"""
        df = pd.read_csv(input_csv_path)
        
        if 'company_name' not in df.columns:
            raise ValueError("CSV must contain 'company_name' column")
        
        enriched_data = []
        total_companies = len(df)
        
        for idx, row in df.iterrows():
            company_name = str(row['company_name']).strip()
            logger.info(f"\n{'='*50}")
            logger.info(f"Processing {idx + 1}/{total_companies}: {company_name}")
            logger.info(f"{'='*50}")
            
            try:
                company_data = self.enrich_company(company_name)
                enriched_data.append({
                    'company_name': company_data.name,
                    'website': company_data.website,
                    'industry': company_data.industry,
                    'summary_from_llm': company_data.summary,
                    'automation_pitch_from_llm': company_data.automation_pitch
                })
            except Exception as e:
                logger.error(f"Critical error processing {company_name}: {e}")
                enriched_data.append({
                    'company_name': company_name,
                    'website': '',
                    'industry': '',
                    'summary_from_llm': f'Processing error: {str(e)}',
                    'automation_pitch_from_llm': ''
                })
        
        output_df = pd.DataFrame(enriched_data)
        output_df.to_csv(output_csv_path, index=False)
        logger.info(f"\n✅ Results saved to {output_csv_path}")
        
        return output_df

def main():
    # Initialize bot
    bot = LeadEnrichmentBot()
    
    # Process CSV
    try:
        result_df = bot.process_csv(DEFAULT_INPUT_FILE, DEFAULT_OUTPUT_FILE)
        print(f"\n🎉 Enrichment completed! Check {DEFAULT_OUTPUT_FILE}")
        print(f"📊 Processed {len(result_df)} companies")
        
        # Show success rate
        successful = len(result_df[result_df['website'] != ''])
        success_rate = (successful / len(result_df)) * 100 if len(result_df) > 0 else 0
        print(f"📈 Success rate: {success_rate:.1f}% ({successful}/{len(result_df)})")
        
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()