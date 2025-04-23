# tunebat_scraper.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import json
import time
import os
from datetime import datetime
import logging
import random
from webdriver_manager.chrome import ChromeDriverManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tunebat_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TunebatScraper:
    def __init__(self):
        # Set up Chrome options
        self.chrome_options = Options()
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Add user agent
        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
        
        # Initialize the Chrome WebDriver
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=self.chrome_options
        )
        
        self.base_url = "https://tunebat.com"
        
        # Create data directory if it doesn't exist
        if not os.path.exists('tunebat_data'):
            os.makedirs('tunebat_data')
            
        # Set up WebDriverWait
        self.wait = WebDriverWait(self.driver, 10)

    def _random_delay(self):
        """Add a random delay between actions"""
        time.sleep(random.uniform(2, 4))

    def _scroll_page(self):
        """Scroll the page to simulate human behavior"""
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(1)
        self.driver.execute_script("window.scrollTo(0, 0);")

    def search_song(self, artist, song):
        """Search for a song on Tunebat"""
        try:
            # Format search URL
            search_query = f"{song} {artist}".replace(' ', '%20')
            search_url = f"{self.base_url}/Search?q={search_query}"
            
            logger.info(f"Searching for: {search_url}")
            print(f"Searching for: {search_url}")
            
            # Navigate to the search URL
            self.driver.get(search_url)
            
            # Wait for page to load and add random delay
            self._random_delay()
            
            # Scroll the page
            self._scroll_page()
            
            # Wait for search results to be present
            try:
                search_results = self.wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/Track/']"))
                )
                
                if search_results:
                    # Click the first result
                    search_results[0].click()
                    self._random_delay()
                    return self.driver.current_url
                
            except TimeoutException:
                logger.warning("No search results found")
                return None
            
        except Exception as e:
            logger.error(f"Error searching for {song} by {artist}: {str(e)}")
            return None

    def get_song_info(self, artist, song):
        """Get detailed information about a song"""
        try:
            # First search for the song
            song_url = self.search_song(artist, song)
            if not song_url:
                raise Exception("Song not found")

            logger.info(f"Getting song info from: {song_url}")
            print(f"Getting song info from: {song_url}")

            # Wait for the page to load
            self._random_delay()
            
            # Initialize song data dictionary
            song_data = {
                "song_name": song,
                "artist": artist,
                "url": song_url,
                "scraped_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "musical_attributes": {},
                "audio_features": {}
            }

            # Wait for the information to be present
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "ant-row"))
                )
            except TimeoutException:
                logger.warning("Could not find song information")
                return None

            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract song information
            info_divs = soup.find_all('div', class_='ant-row')
            for div in info_divs:
                label = div.find('div', class_='Label__LabelDiv-sc-15fxapi-0')
                value = div.find('div', class_='Value__ValueDiv-sc-1zxzxfr-0')
                
                if label and value:
                    label_text = label.get_text().strip().lower()
                    value_text = value.get_text().strip()
                    
                    print(f"Found {label_text}: {value_text}")
                    
                    # Categorize the information
                    if label_text in ['key', 'bpm', 'camelot']:
                        song_data["musical_attributes"][label_text] = value_text
                    else:
                        song_data["audio_features"][label_text] = value_text

            return song_data

        except Exception as e:
            logger.error(f"Error getting info for {song} by {artist}: {str(e)}")
            return None

    def save_song_info(self, song_data, output_dir='tunebat_data'):
        """Save song information to a JSON file"""
        if song_data:
            try:
                filename = f"{song_data['artist'].replace(' ', '_')}_{song_data['song_name'].replace(' ', '_')}.json"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(song_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Saved data to {filepath}")
                return filepath
            except Exception as e:
                logger.error(f"Error saving data: {str(e)}")
                return None
        return None

    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()

def main():
    scraper = None
    try:
        # Initialize scraper
        scraper = TunebatScraper()
        
        # Example songs to scrape
        songs_to_scrape = [
            {"artist": "Rod Wave", "song": "25"}
        ]
        
        for song_info in songs_to_scrape:
            print(f"\nScraping data for '{song_info['song']}' by {song_info['artist']}...")
            
            # Get song information
            song_data = scraper.get_song_info(song_info['artist'], song_info['song'])
            
            if song_data:
                # Save to file
                saved_file = scraper.save_song_info(song_data)
                if saved_file:
                    print(f"Data saved to: {saved_file}")
                    
                    # Print some key information
                    print("\nKey Information:")
                    if "musical_attributes" in song_data:
                        for key, value in song_data["musical_attributes"].items():
                            print(f"{key.upper()}: {value}")
                    
                    print("\nAudio Features:")
                    if "audio_features" in song_data:
                        for key, value in song_data["audio_features"].items():
                            print(f"{key.title()}: {value}")
            else:
                print(f"Failed to get data for {song_info['song']} by {song_info['artist']}")
    
    finally:
        # Make sure to close the browser
        if scraper:
            scraper.close()

if __name__ == "__main__":
    main()