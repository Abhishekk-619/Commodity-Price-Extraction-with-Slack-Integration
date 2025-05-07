import json
import re
import requests
import time
from bs4 import BeautifulSoup

class EggPriceAgentFireCrawl:
    def __init__(self):
        self.base_url = "https://eggpricetoday.com/"
        # Store the city-wise egg prices
        self.city_prices = {}
        # User agent for web requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Initialize with the data provided by the user
        self.initialize_city_prices()
    
    def initialize_city_prices(self):
        """Initialize the city prices by scraping the latest data from eggpricetoday.com"""
        # First try to fetch real-time data from the website
        scraped_data = self.scrape_egg_prices()
        
        if scraped_data and len(scraped_data) > 0:
            # If scraping was successful, use the scraped data
            self.city_prices = scraped_data
        else:
            # Fallback to hardcoded data if scraping fails
            city_data = {
                "Ahmedabad": {"1pc": "₹4.15", "30pcs": "₹124.5", "100pcs": "₹415", "210pcs": "₹871.5"},
                "Ajmer": {"1pc": "₹3.75", "30pcs": "₹112.5", "100pcs": "₹375", "210pcs": "₹787.5"},
                "Barwala": {"1pc": "₹3.95", "30pcs": "₹118.5", "100pcs": "₹395", "210pcs": "₹829.5"},
                "Bengaluru": {"1pc": "₹4.50", "30pcs": "₹135", "100pcs": "₹450", "210pcs": "₹945"},
                "Brahmapur": {"1pc": "₹4.10", "30pcs": "₹123", "100pcs": "₹410", "210pcs": "₹861"},
                "Chennai": {"1pc": "₹4.60", "30pcs": "₹138", "100pcs": "₹460", "210pcs": "₹966"},
                "Chittoor": {"1pc": "₹4.60", "30pcs": "₹138", "100pcs": "₹460", "210pcs": "₹966"},
                "Delhi": {"1pc": "₹4.10", "30pcs": "₹123", "100pcs": "₹410", "210pcs": "₹861"},
                "E-godavari": {"1pc": "₹4.15", "30pcs": "₹124.5", "100pcs": "₹415", "210pcs": "₹871.5"},
                "Hospet": {"1pc": "₹3.95", "30pcs": "₹118.5", "100pcs": "₹395", "210pcs": "₹829.5"},
                "Hyderabad": {"1pc": "₹3.90", "30pcs": "₹117", "100pcs": "₹390", "210pcs": "₹819"},
                "Jabalpur": {"1pc": "₹4.05", "30pcs": "₹121.5", "100pcs": "₹405", "210pcs": "₹850.5"},
                "Kolkata": {"1pc": "₹4.50", "30pcs": "₹135", "100pcs": "₹450", "210pcs": "₹945"},
                "Ludhiana": {"1pc": "₹3.95", "30pcs": "₹118.5", "100pcs": "₹395", "210pcs": "₹829.5"},
                "Mumbai": {"1pc": "₹4.50", "30pcs": "₹135", "100pcs": "₹450", "210pcs": "₹945"},
                "Mysuru": {"1pc": "₹4.50", "30pcs": "₹135", "100pcs": "₹450", "210pcs": "₹945"},
                "Namakkal": {"1pc": "₹4.15", "30pcs": "₹124.5", "100pcs": "₹415", "210pcs": "₹871.5"},
                "Pune": {"1pc": "₹4.40", "30pcs": "₹132", "100pcs": "₹440", "210pcs": "₹924"},
                "Raipur": {"1pc": "₹4.10", "30pcs": "₹123", "100pcs": "₹410", "210pcs": "₹861"},
                "Surat": {"1pc": "₹4.35", "30pcs": "₹130.5", "100pcs": "₹435", "210pcs": "₹913.5"},
                "Vijayawada": {"1pc": "₹4.20", "30pcs": "₹126", "100pcs": "₹420", "210pcs": "₹882"},
                "Vizag": {"1pc": "₹4.35", "30pcs": "₹130.5", "100pcs": "₹435", "210pcs": "₹913.5"},
                "W-godavari": {"1pc": "₹4.15", "30pcs": "₹124.5", "100pcs": "₹415", "210pcs": "₹871.5"},
                "Warangal": {"1pc": "₹3.92", "30pcs": "₹117.6", "100pcs": "₹392", "210pcs": "₹823.2"},
                "Allahabad": {"1pc": "₹4.38", "30pcs": "₹131.4", "100pcs": "₹438", "210pcs": "₹919.8"},
                "Bhopal": {"1pc": "₹3.90", "30pcs": "₹117", "100pcs": "₹390", "210pcs": "₹819"},
                "Indore": {"1pc": "₹4.00", "30pcs": "₹120", "100pcs": "₹400", "210pcs": "₹840"},
                "Kanpur": {"1pc": "₹4.38", "30pcs": "₹131.4", "100pcs": "₹438", "210pcs": "₹919.8"},
                "Luknow": {"1pc": "₹4.67", "30pcs": "₹140.1", "100pcs": "₹467", "210pcs": "₹980.7"},
                "Muzaffurpur": {"1pc": "₹4.60", "30pcs": "₹138", "100pcs": "₹460", "210pcs": "₹966"}
            }
            self.city_prices = city_data

    def scrape_egg_prices(self):
        """Scrape egg prices from eggpricetoday.com"""
        try:
            # Fetch the webpage with a fresh request each time - no caching
            response = requests.get(
                self.base_url, 
                headers=self.headers, 
                timeout=10,
                params={'_': str(int(time.time()))},  # Add timestamp to prevent caching
            )
            response.raise_for_status()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # First try to find any price data in divs or spans
            city_prices = self.extract_prices_from_elements(soup)
            if city_prices:
                return city_prices
            
            # If no prices found in divs/spans, try tables
            tables = soup.find_all('table')
            if not tables:
                print("No tables found on the website")
                return self.scrape_alternative_method(soup)
            
            city_prices = {}
            print("Scraping latest egg prices from website...")
            
            # Try each table until we find price data
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    # Look for both th and td cells to handle different table structures
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 4:  # Need at least city name and some prices
                        city_name = cells[0].text.strip()
                        if city_name and city_name.lower() not in ['city', 'location', '']:
                            # Try to extract prices, handling different formats
                            prices = []
                            for cell in cells[1:5]:  # Get up to 4 price cells
                                price_text = cell.text.strip()
                                # Try to find a price value in the cell
                                price_match = re.search(r'(?:₹)?\s*([\d.]+)', price_text)
                                if price_match:
                                    price = price_match.group(1)
                                    prices.append(f"₹{price}" if not price.startswith('₹') else price)
                                else:
                                    prices.append(None)
                            
                            # Only add city if we found at least one valid price
                            if any(prices):
                                # Pad prices list if needed
                                while len(prices) < 4:
                                    prices.append(None)
                                
                                # Process prices for all cities including Mumbai
                                if city_name.lower() == 'mumbai':
                                    # Use the actual scraped prices for Mumbai
                                    if prices[0]:
                                        piece_price = prices[0]
                                        price_value = float(re.search(r'[\d.]+', piece_price).group())
                                        prices[1] = f"₹{price_value * 30:.2f}"
                                        prices[2] = f"₹{price_value * 100:.2f}"
                                        prices[3] = f"₹{price_value * 210:.2f}"
                                
                                city_prices[city_name] = {
                                    "1pc": prices[0] or "N/A",
                                    "30pcs": prices[1] or "N/A",
                                    "100pcs": prices[2] or "N/A",
                                    "210pcs": prices[3] or "N/A"
                                }
            
            if city_prices:
                print(f"Successfully scraped prices for {len(city_prices)} cities")
                return city_prices
            else:
                print("No city prices found in tables")
                return self.scrape_alternative_method(soup)
                
        except Exception as e:
            print(f"Error scraping egg prices: {str(e)}")
            return {}
            
    def extract_prices_from_elements(self, soup):
        """Extract prices from div and span elements"""
        try:
            city_prices = {}
            
            # Look for elements that might contain price information
            price_containers = soup.find_all(['div', 'span', 'p'], class_=lambda x: x and any(word in x.lower() for word in ['price', 'rate', 'cost']))
            
            for container in price_containers:
                text = container.text.lower()
                # Look for city names and prices
                for city in self.city_prices.keys():  # Use existing city list as reference
                    if city.lower() in text:
                        price_match = re.search(r'(?:₹)?\s*([\d.]+)', text)
                        if price_match:
                            price = price_match.group(1)
                            piece_price = f"₹{price}" if not price.startswith('₹') else price
                            
                            # Process price for all cities including Mumbai
                            if city.lower() == 'mumbai':
                                piece_price = price_match.group(1)
                                price = piece_price
                            
                            # Calculate other quantities based on piece price
                            price_value = float(price)
                            city_prices[city] = {
                                "1pc": piece_price,
                                "30pcs": f"₹{price_value * 30:.2f}",
                                "100pcs": f"₹{price_value * 100:.2f}",
                                "210pcs": f"₹{price_value * 210:.2f}"
                            }
            
            return city_prices
            
        except Exception as e:
            print(f"Error extracting prices from elements: {str(e)}")
            return {}
            
    def scrape_alternative_method(self, soup):
        """Alternative method to scrape prices if table approach fails"""
        try:
            city_prices = {}
            
            # Look for price information in any elements with rupee symbol
            price_elements = soup.find_all(string=lambda text: text and '₹' in text)
            
            # Try to find city names and associated prices
            for element in price_elements:
                parent = element.parent
                parent_text = parent.text.strip()
                
                # Check if this contains Mumbai price
                if 'mumbai' in parent_text.lower():
                    # Try to extract the price
                    price_match = re.search(r'₹(\d+(\.\d+)?)', parent_text)
                    if price_match:
                        price = price_match.group(1)
                        print(f"Found Mumbai price via alternative method: ₹{price}")
                        
                        # Create entry for Mumbai with the correct price
                        city_prices['Mumbai'] = {
                            "1pc": f"₹{price}",
                            "30pcs": f"₹{float(price)*30}",
                            "100pcs": f"₹{float(price)*100}",
                            "210pcs": f"₹{float(price)*210}"
                        }
            
            return city_prices
            
        except Exception as e:
            print(f"Error in alternative scraping: {str(e)}")
            return {}
    
    def fetch_egg_prices(self):
        """Fetch fresh egg prices by scraping the website"""
        try:
            # Always try to get fresh data first
            scraped_data = self.scrape_egg_prices()
            if scraped_data:
                self.city_prices = scraped_data
                return self.city_prices
            
            # Fallback to cached data only if scraping fails
            return self.city_prices
                
        except Exception as e:
            return {"error": f"An error occurred while fetching egg prices: {str(e)}"}
    
    def process_query(self, query):
        """Process user query about egg prices"""
        query = query.lower()
        
        # Check if the query is asking about egg prices
        if any(keyword in query for keyword in ['egg price', 'price of egg', 'how much', 'cost', 'rate', 'eggs cost', 'price', 'prices']):
            prices = self.fetch_egg_prices()
            
            if "error" in prices:
                return prices["error"]
            
            # Check if query is for a specific city
            city_mentioned = None
            for city in prices.keys():
                if city.lower() in query:
                    city_mentioned = city
                    break
            
            # Check if query is for a specific quantity
            quantity_mentioned = None
            quantity_patterns = {
                '1pc': ['1 egg', 'single egg', 'one egg', 'per egg', 'each egg', 'price of an egg', 'price of 1 egg', 'price of one egg'],
                '30pcs': ['30 eggs', 'thirty eggs', 'tray', 'price of tray', 'tray price', 'price of 30 eggs', 'thirty', '30'],
                '100pcs': ['100 eggs', 'hundred eggs', 'one hundred eggs', 'price of 100 eggs', 'hundred', '100'],
                '210pcs': ['210 eggs', 'two hundred ten eggs', 'box', 'price of box', 'box price', 'price of 210 eggs', '210']
            }
            
            for qty, patterns in quantity_patterns.items():
                if any(pattern in query for pattern in patterns):
                    quantity_mentioned = qty
                    break
            
            # Format the response based on whether a city and/or quantity was mentioned
            if city_mentioned:
                if quantity_mentioned:
                    # Both city and quantity specified
                    price = prices[city_mentioned][quantity_mentioned]
                    return f"The price for {quantity_mentioned} in {city_mentioned} is {price}."
                else:
                    # Only city specified
                    response = f"Here are the current egg prices in {city_mentioned}:\n"
                    for quantity, price in prices[city_mentioned].items():
                        quantity_desc = {
                            '1pc': 'Single egg',
                            '30pcs': 'Tray (30 eggs)',
                            '100pcs': '100 eggs',
                            '210pcs': 'Box (210 eggs)'
                        }.get(quantity, quantity)
                        response += f"- {quantity_desc}: {price}\n"
                    return response
            else:
                # If no specific city mentioned, show prices for a few major cities
                major_cities = ["Delhi", "Mumbai", "Bengaluru", "Chennai", "Hyderabad", "Kolkata"]
                response = "Here are the current egg prices in major cities (price per egg):\n"
                for city in major_cities:
                    if city in prices:
                        response += f"- {city}: {prices[city]['1pc']}\n"
                response += "\nYou can ask for prices in a specific city, for example: 'What is the egg price in Pune?'"
                response += "\nOr ask for specific quantities like: 'How much do 30 eggs cost in Delhi?' or 'What is the price of a tray in Mumbai?'"
                return response
        elif any(keyword in query for keyword in ['city', 'cities', 'location', 'where']):
            # If user is asking about available cities
            prices = self.fetch_egg_prices()
            cities = list(prices.keys())
            response = "I have egg price information for the following cities:\n"
            # Format cities in columns for better readability
            for i in range(0, len(cities), 3):
                row_cities = cities[i:i+3]
                response += ", ".join(row_cities) + "\n"
            return response
        else:
            return "I can help you find out the current price of eggs in various cities across India. Please ask me about egg prices, for example: 'What is the egg price in Mumbai?' or 'Show me egg prices in major cities.'"


def main():
    agent = EggPriceAgentFireCrawl()
    print("=" * 60)
    print("🥚 Egg Price Agent (India) 🥚")
    print("=" * 60)
    print("Type 'exit' to quit.")
    print("\nAsk me about egg prices, for example:")
    print("  - 'What is the price of eggs in Mumbai?'")
    print("  - 'Show me egg prices in Delhi'")
    print("  - 'Which cities do you have egg price data for?'")
    print("  - 'How much do 100 eggs cost in Bengaluru?'")
    print("  - 'What is the price of a tray in Chennai?'")
    print("  - 'Show me current egg rates'")
    
    while True:
        user_input = input("\nYour question: ")
        
        if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
            print("\nThank you for using the Egg Price Agent. Goodbye!")
            break
        
        response = agent.process_query(user_input)
        print(f"\nAgent: {response}")


if __name__ == "__main__":
    main()