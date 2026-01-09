import time
import random
import logging
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JobScraper:
    def __init__(self, headless=True):
        self.options = Options()
        if headless:
            self.options.add_argument("--headless")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--window-size=1920,1080")
        # Anti-detection: User Agent
        self.options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)

    def scrape_linkedin(self, job_title="Data Scientist", location="United States", limit=10):
        """
        Scrapes job listings from LinkedIn public job search page.
        """
        logger.info(f"Starting scraping for {job_title} in {location}...")
        
        # Prepare URL (LinkedIn Guest Job Search)
        base_url = "https://www.linkedin.com/jobs/search"
        params = f"?keywords={job_title.replace(' ', '%20')}&location={location.replace(' ', '%20')}"
        url = base_url + params
        
        self.driver.get(url)
        time.sleep(random.uniform(3, 5)) # Wait for initial load

        jobs_data = []
        
        try:
            # Scroll to load more jobs
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            for _ in range(3): 
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 3))
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            # Find job cards
            job_cards = self.driver.find_elements(By.CLASS_NAME, 'base-card')
            logger.info(f"Found {len(job_cards)} job cards. Processing top {limit}...")

            for i, card in enumerate(job_cards[:limit]):
                try:
                    # Get the link first, as it's the most important
                    link = card.find_element(By.TAG_NAME, 'a').get_attribute('href')
                    
                    jobs_data.append({
                        "link": link,
                        "source": "LinkedIn"
                    })
                except Exception as e:
                    logger.warning(f"Failed to parse card {i}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error during scraping list: {e}")
            
        return pd.DataFrame(jobs_data)

    def get_job_details(self, url):
        """
        Visits the job URL and extracts detailed description and metadata.
        """
        try:
            self.driver.get(url)
            time.sleep(random.uniform(2, 4)) # Random sleep to be polite
            
            details = {}
            
            # Try to get Title
            try:
                details['title'] = self.driver.find_element(By.CLASS_NAME, 'top-card-layout__title').text.strip()
            except:
                details['title'] = None

            # Try to get Company
            try:
                details['company'] = self.driver.find_element(By.CLASS_NAME, 'topcard__org-name-link').text.strip()
            except:
                details['company'] = None

            # Try to get Location
            try:
                details['location'] = self.driver.find_element(By.CLASS_NAME, 'topcard__flavor--bullet').text.strip()
            except:
                details['location'] = None
                
            # Try to get Description (Try multiple selectors as LinkedIn changes often)
            try:
                # Click "Show more" if button exists (sometimes needed)
                try:
                    show_more_btn = self.driver.find_element(By.CLASS_NAME, 'show-more-less-html__button--more')
                    show_more_btn.click()
                    time.sleep(1)
                except:
                    pass
                
                description_div = self.driver.find_element(By.CLASS_NAME, 'show-more-less-html__markup')
                details['description'] = description_div.get_attribute("innerText") # innerText preserves newlines better
                
            except Exception:
                # Fallback selector
                try:
                    details['description'] = self.driver.find_element(By.CLASS_NAME, 'description__text').text
                except:
                    details['description'] = None

            return details
            
        except Exception as e:
            logger.error(f"Error visiting {url}: {e}")
            return None

    def run(self, job_title="Data Scientist", location="United States", limit=5):
        # 1. Get List of Jobs
        df = self.scrape_linkedin(job_title, location, limit)
        if df.empty:
            logger.warning("No jobs found.")
            return df
        
        logger.info(f"Successfully collected {len(df)} links. Now scraping details...")
        
        # 2. Visit each link to get details
        detailed_data = []
        for index, row in df.iterrows():
            logger.info(f"Scraping job {index + 1}/{len(df)}: {row['link'][:50]}...")
            details = self.get_job_details(row['link'])
            
            if details:
                # Merge link info with details
                details['link'] = row['link']
                details['source'] = row['source']
                detailed_data.append(details)
            else:
                logger.warning(f"Skipping {row['link']}")
        
        # 3. Create final DataFrame
        final_df = pd.DataFrame(detailed_data)
        self.driver.quit()
        return final_df

    def save_data(self, df, filename="data/raw/jobs.csv"):
        df.to_csv(filename, index=False)
        logger.info(f"Data saved to {filename}")

if __name__ == "__main__":
    scraper = JobScraper(headless=True)
    # Testing with a small limit first
    df = scraper.run(job_title="Data Scientist", location="United States", limit=5)
    
    print("\n--- Scraping Result ---")
    print(df.info())
    print(df[['title', 'company']].head())
    
    # Save if data exists
    if not df.empty:
        scraper.save_data(df)

