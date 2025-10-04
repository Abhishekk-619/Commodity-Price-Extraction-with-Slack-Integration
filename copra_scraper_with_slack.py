"""
Copra Price Scraper with Slack Notifications
============================================

Enhanced version of the copra price scraper with integrated Slack notifications.
Sends success/error messages to Slack channel automatically.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, UTC
from pymongo import MongoClient
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import logging
import traceback
from slack_notifier import SlackNotifier


class CopraPriceScraperWithSlack:
    """Copra price scraper with Slack notification integration"""
    
    def __init__(self):
        """Initialize the scraper with Slack notifications"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504, 429],
            allowed_methods=["GET"]
        )
        
        # Create session with retry strategy
        self.session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.cities = ['bangalore', 'chennai', 'mumbai', 'delhi', 'hyderabad', 'kolkata', 'pune', 'thiruvananthapuram', 'surat', 'kochi', 'coimbatore', 'mangaluru', 'visakhapatnam', 'madurai', 'kozhikode', 'ahmedabad', 'gandhidham', 'bhadohi', 'indore', 'pollachi', 'tiptur', 'secunderabad', 'mandya', 'namakkal', 'erode', 'mysore', 'thane', 'cuttack', 'karikkad', 'doiwala', 'jaipur', 'agra', 'gurugram', 'loni', 'kanpur', 'tumakuru', 'hosur', 'vasai-virar', 'panvel', 'nashik', 'karjat', 'vellakovil', 'udumalpet', 'hassan', 'salem', 'hubli', 'gobichettipalayam', 'nagpur', 'raipur', 'patna', 'amritsar', 'noida', 'rajkot', 'varanasi', 'lucknow', 'bhopal', 'theni-allinagaram', 'navi-mumbai', 'new-delhi']
        self.prices = {}
        
        # MongoDB connection
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['egg_price_data']
        self.prices_collection = self.db['copra_prices']
        
        # Slack notifier
        self.slack = SlackNotifier()
        self.scraper_name = "COPRA SCRAPER"

    def _extract_price(self, text):
        """Extract price value from text and standardize to price per kg"""
        try:
            import re
            numbers = re.findall(r'\d+(?:,\d+)*(?:\.\d+)?', text)
            if numbers:
                price = float(numbers[0].replace(',', ''))
                if 'quintal' in text.lower() or 'qtl' in text.lower():
                    price = price / 100
                elif 'ton' in text.lower():
                    price = price / 1000
                return price
        except Exception as e:
            print(f'Error extracting price from {text}: {str(e)}')
        return None

    def scrape_indiamart(self):
        """Scrape prices from IndiaMART"""
        try:
            for city in self.cities:
                print(f'Scraping Coconut Copra prices for {city}...')
                url = f'https://dir.indiamart.com/{city}/coconut-copra.html'
                try:
                    response = self.session.get(url, headers=self.headers, timeout=30)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    logging.error(f'Error scraping {city}: {str(e)}')
                    time.sleep(5)
                    continue
                    
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    price_data = {
                        'min_price': None,
                        'max_price': None,
                        'avg_price': None,
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'source': 'IndiaMART'
                    }

                    # Find price elements
                    price_elements = soup.find_all('span', class_='prc')
                    prices = [self._extract_price(elem.text) for elem in price_elements if elem]
                    prices = [p for p in prices if p is not None]

                    if prices:
                        price_data['min_price'] = min(prices)
                        price_data['max_price'] = max(prices)
                        price_data['avg_price'] = sum(prices) / len(prices)

                    if not self.prices.get(city):
                        self.prices[city] = price_data
                    elif any(price_data.values()):
                        self.prices[city].update(price_data)
                else:
                    print(f'Failed to fetch data for {city} from IndiaMART (Status code: {response.status_code})')
        except Exception as e:
            print(f'Error scraping IndiaMART: {str(e)}')
            raise

    def save_to_mongodb(self):
        """Save the scraped prices to MongoDB"""
        try:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            documents = []
            skipped_cities = []
            
            for city, data in self.prices.items():
                if data.get('min_price') is not None:
                    existing_record = self.prices_collection.find_one({
                        'city': city,
                        'commodity': 'copra',
                        'price_date': today
                    })
                    
                    if existing_record:
                        skipped_cities.append(city)
                        continue
                        
                    document = {
                        'city': city,
                        'commodity': 'copra',
                        'min_price': data['min_price'],
                        'max_price': data['max_price'],
                        'avg_price': data['avg_price'],
                        'price_date': today,
                        'timestamp': datetime.now(UTC)
                    }
                    documents.append(document)
            
            if documents:
                self.prices_collection.insert_many(documents)
                print(f'Successfully saved {len(documents)} price records to MongoDB')
                return True
            else:
                if skipped_cities:
                    print(f'Skipped {len(skipped_cities)} cities as data already exists for today')
                else:
                    print('No valid price data to save to MongoDB')
                return False

        except Exception as e:
            print(f'Error saving to MongoDB: {str(e)}')
            raise

    def run_scraping(self):
        """
        Run the copra price scraping with Slack notifications
        
        Returns:
            bool: True if scraping succeeded, False if failed
        """
        try:
            print('Starting copra price scraping from IndiaMART...')
            
            # Scrape prices
            self.scrape_indiamart()
            
            # Check if we got any data
            if not any(self.prices.values()):
                print('❌ Copra scraping failed - no price data collected!')
                self.slack.send_error(self.scraper_name)
                return False
            
            # Save to MongoDB
            save_success = self.save_to_mongodb()
            
            if save_success:
                print('✅ Copra scraping completed successfully!')
                self.slack.send_success(self.scraper_name)
                return True
            else:
                print('⚠️ Copra scraping completed but no new data saved (may already exist)')
                self.slack.send_success(self.scraper_name)  # Still consider it success
                return True
                
        except Exception as e:
            print(f'❌ Copra scraping failed with error: {str(e)}')
            print("Full error traceback:")
            traceback.print_exc()
            self.slack.send_error(self.scraper_name)
            return False

    def close(self):
        """Close database connections"""
        try:
            if hasattr(self, 'client'):
                self.client.close()
        except:
            pass


def main():
    """Main function to run copra scraper with Slack notifications"""
    scraper = None
    try:
        print("=" * 60)
        print("🥥 Copra Price Scraper with Slack Notifications 🥥")
        print("=" * 60)
        
        # Initialize and run scraper
        scraper = CopraPriceScraperWithSlack()
        success = scraper.run_scraping()
        
        if success:
            print("\n✅ Copra price scraping completed successfully!")
        else:
            print("\n❌ Copra price scraping failed!")
            
    except Exception as e:
        print(f"\n❌ Critical error in copra scraper: {str(e)}")
        traceback.print_exc()
        
        # Send error notification
        if scraper and hasattr(scraper, 'slack'):
            scraper.slack.send_error("COPRA SCRAPER")
        else:
            slack = SlackNotifier()
            slack.send_error("COPRA SCRAPER")
    
    finally:
        # Clean up
        if scraper:
            scraper.close()


if __name__ == '__main__':
    main()
