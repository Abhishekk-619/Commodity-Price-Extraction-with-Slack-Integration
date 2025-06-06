import requests
from bs4 import BeautifulSoup
from datetime import datetime, UTC
from pymongo import MongoClient
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class CopraPriceScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=5,  # number of retries
            backoff_factor=1,  # wait 1, 2, 4, 8, 16 seconds between retries
            status_forcelist=[500, 502, 503, 504, 429],  # HTTP status codes to retry on
            allowed_methods=["GET"]  # HTTP methods to retry
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



    def _extract_price(self, text):
        """Extract price value from text and standardize to price per kg"""
        try:
            # Find numbers and units in the text
            import re
            numbers = re.findall(r'\d+(?:,\d+)*(?:\.\d+)?', text)
            if numbers:
                price = float(numbers[0].replace(',', ''))
                # Convert to price per kg if needed
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
                    time.sleep(5)  # Wait before trying next city
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



    def save_to_mongodb(self):
        """Save the scraped prices to MongoDB if no data exists for today"""
        try:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            documents = []
            skipped_cities = []
            
            for city, data in self.prices.items():
                if data.get('min_price') is not None:
                    # Check if data already exists for this city today
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
            else:
                if skipped_cities:
                    print(f'Skipped {len(skipped_cities)} cities as data already exists for today: {", ".join(skipped_cities)}')
                else:
                    print('No valid price data to save to MongoDB')

        except Exception as e:
            print(f'Error saving to MongoDB: {str(e)}')

    def run(self):
        """Run the scraper"""
        print('Starting copra price scraping from IndiaMART...')
        self.scrape_indiamart()
        
        if not any(self.prices.values()):
            print('\nWarning: No price data was collected!')
        else:
            print('\nSaving results...')
            self.save_to_mongodb()
        
        print('\nScraping completed!')


if __name__ == '__main__':
    scraper = CopraPriceScraper()
    scraper.run()