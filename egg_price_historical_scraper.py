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
        # Store historical data for each city
        self.historical_data = {city: [] for city in self.city_urls}
        # Track last update date for each city
        self.last_update_dates = {city: None for city in self.city_urls}
    
    def fetch_historical_prices(self, city):
        """Fetch historical egg prices for a specific city
        
        Args:
            city (str): Name of the city (lowercase)
            
        Returns:
            list: List of dictionaries containing historical price data
        """
        if city not in self.city_urls:
            return []
            
        # Check if we already have today's data
        today = datetime.now().date()
        
        # Check if we have any historical data and if the most recent entry is from today
        if self.historical_data[city] and self.historical_data[city][0]['date'] == today:
            print(f"Already have today's data for {city}, skipping update")
            return self.historical_data[city]
        
        # Check if we already have an update for today
        if self.last_update_dates[city] == today:
            print(f"Already updated data for {city} today, skipping fetch")
            return self.historical_data[city]
        
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
                                    
                                    # Update last update date if this is today's data
                                    if date == today:
                                        self.last_update_dates[city] = today
                        except (ValueError, TypeError):
                            continue
            
            # Sort by date in descending order
            historical_data.sort(key=lambda x: x['date'], reverse=True)
            
            # Get existing dates in historical data
            existing_dates = {item['date'] for item in self.historical_data[city]}
            
            # Only add new data points that don't exist in historical data
            new_data = [data for data in historical_data if data['date'] not in existing_dates and all(v > 0 for v in data['rates'].values())]
            
            # Create a new list combining existing and new data without duplicates
            combined_data = []
            seen_dates = set()
            
            # First add existing data (preserving original values)
            for item in self.historical_data[city]:
                if item['date'] not in seen_dates:
                    combined_data.append(item)
                    seen_dates.add(item['date'])
            
            # Then add new data only if date not already present
            for item in new_data:
                if item['date'] not in seen_dates:
                    combined_data.append(item)
                    seen_dates.add(item['date'])
            
            # Sort and limit to last 30 days
            combined_data.sort(key=lambda x: x['date'], reverse=True)
            self.historical_data[city] = combined_data[:30]
            
            return self.historical_data[city]
            
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