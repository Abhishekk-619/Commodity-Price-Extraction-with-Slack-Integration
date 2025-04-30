import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

class EggPriceHistoricalScraper:
    def __init__(self):
        self.base_url = "https://eggpricetoday.com/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.city_urls = {
            'mumbai': 'mumbai-egg-rate-today',
            'delhi': 'delhi-egg-rate-today',
            'bengaluru': 'bengaluru-egg-rate-today',  # Map Bengaluru to the same URL
            'chennai': 'chennai-egg-rate-today',
            'hyderabad': 'hyderabad-egg-rate-today',
            'kolkata': 'kolkata-egg-rate-today'
        }
    
    def fetch_historical_prices(self, city):
        """Fetch historical egg prices for a specific city
        
        Args:
            city (str): Name of the city (lowercase)
            
        Returns:
            list: List of dictionaries containing historical price data
        """
        if city not in self.city_urls:
            return []
        
        try:
            url = f"{self.base_url}{self.city_urls[city]}"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            historical_data = []
            
            # Find the historical price table
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:  # Skip header row
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        date_text = cells[0].text.strip()
                        price_text = cells[1].text.strip()
                        
                        try:
                            # Extract date
                            date = datetime.strptime(date_text, '%d-%m-%Y').date()
                            
                            # Extract price, handling various formats
                            # Remove rupee symbol and any non-numeric characters except decimal point
                            price_str = ''.join(c for c in price_text if c.isdigit() or c == '.')
                            
                            # Ensure the string is not empty and doesn't end with a decimal point
                            if price_str and not price_str.endswith('.'):
                                try:
                                    price = float(price_str)
                                except ValueError:
                                    continue
                                if price > 0:
                                    # Calculate prices for different quantities
                                    historical_data.append({
                                        'date': date,
                                        'rates': {
                                            'single_egg': price,
                                            'tray': price * 30,
                                            'hundred_eggs': price * 100,
                                            'box': price * 210
                                        }
                                    })
                        except (ValueError, TypeError):
                            continue
            
            # Sort by date in descending order and get last 30 days
            historical_data.sort(key=lambda x: x['date'], reverse=True)
            # Filter out any invalid or zero prices
            valid_data = [data for data in historical_data[:30] if all(v > 0 for v in data['rates'].values())]
            return valid_data
            
        except Exception as e:
            print(f"Error fetching historical prices for {city}: {str(e)}")
            return []
    
    def fetch_all_cities_historical(self):
        """Fetch historical prices for all supported cities
        
        Returns:
            dict: Dictionary with city names as keys and their historical data as values
        """
        all_historical = {}
        for city in self.city_urls:
            all_historical[city] = self.fetch_historical_prices(city)
        return all_historical