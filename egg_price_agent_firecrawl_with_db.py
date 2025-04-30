from egg_price_agent_firecrawl import EggPriceAgentFireCrawl
from egg_price_schema import EggPriceDatabase
from egg_price_historical_scraper import EggPriceHistoricalScraper
from datetime import datetime
import re

"""
Egg Price Agent FireCrawl with MongoDB Integration

This module extends the original EggPriceAgentFireCrawl with database functionality
to store egg prices with timestamps in MongoDB.
"""


class EggPriceAgentFireCrawlWithDB:
    def __init__(self, connection_string="mongodb://localhost:27017/", db_name="egg_price_data"):
        """
        Initialize the agent with database integration
        
        Args:
            connection_string (str): MongoDB connection string
            db_name (str): Name of the database
        """
        self.agent = EggPriceAgentFireCrawl()
        self.historical_scraper = EggPriceHistoricalScraper()
        self.db = EggPriceDatabase(connection_string, db_name)
        self._store_initial_prices()
        self._store_historical_prices()
    
    def _store_initial_prices(self):
        """Store current egg prices in MongoDB for specified cities only"""
        allowed_cities = {
            'bengaluru': 'bengaluru',  # Handle both names
            'chennai': 'chennai',
            'mumbai': 'mumbai',
            'hyderabad': 'hyderabad',
            'hyd': 'hyderabad',  # Handle abbreviation
            'kolkata': 'kolkata',
            'kol': 'kolkata',  # Handle abbreviation
            'delhi': 'delhi'
        }
        
        try:
            prices = self.agent.fetch_egg_prices()
            if prices and isinstance(prices, dict) and 'error' not in prices:
                for city, price_data in prices.items():
                    city_lower = city.lower()
                    if city_lower in allowed_cities:
                        normalized_city = allowed_cities[city_lower]
                        # Clean and validate price data before storing
                        cleaned_data = self._clean_price_data(price_data)
                        if cleaned_data:
                            self.db.store_egg_prices(normalized_city, cleaned_data)
        except Exception as e:
            print(f"Error scraping egg prices: {e}")

    def _clean_price_data(self, price_data):
        """Clean and validate price data before storing"""
        try:
            cleaned = {}
            for key, value in price_data.items():
                if isinstance(value, str):
                    # Remove rupee symbol and any non-numeric characters except decimal point
                    price_str = ''.join(c for c in value if c.isdigit() or c == '.')
                    # Additional validation to handle lone decimal points
                    if price_str and not price_str.endswith('.') and not price_str.startswith('.'):
                        # Check if there's exactly one decimal point
                        if price_str.count('.') <= 1:
                            try:
                                price_float = float(price_str)
                                if price_float > 0:  # Only accept positive values
                                    cleaned[key] = price_float
                            except ValueError:
                                continue
            return cleaned if cleaned else None
        except Exception as e:
            print(f"Error cleaning price data: {e}")
            return None
    
    def process_query(self, query):
        """
        Process a user query about egg prices
        
        Args:
            query (str): The user's query about egg prices
            
        Returns:
            str: The agent's response
        """
        # Get response from the original agent
        response = self.agent.process_query(query)
        return response
    
    def _extract_city_from_query(self, query):
        """
        Extract city name from the query if present
        
        Args:
            query (str): The user's query
            
        Returns:
            str or None: City name if found, None otherwise
        """
        query = query.lower()
        
        # Get list of cities from the agent
        cities = list(self.agent.city_prices.keys())
        
        # Check if any city is mentioned in the query
        for city in cities:
            if city.lower() in query:
                return city.lower()
        
        return None
    
    def _extract_price_data(self, response):
        """
        Extract structured price data from the response if possible
        
        Args:
            response (str): The agent's response
            
        Returns:
            dict or None: Structured price data if extractable, None otherwise
        """
        price_data = {}
        
        try:
            lines = response.split('\n')
            for line in lines:
                if ':' in line and line.strip().startswith('-'):
                    # Extract price information from lines like "- Single egg: ₹7"
                    parts = line.strip()[2:].split(':', 1)  # Remove the leading "- " and split on first colon
                    if len(parts) == 2:
                        key = parts[0].strip().lower()
                        value = parts[1].strip()
                        price_data[key] = value
            
            return price_data if price_data else None
        except Exception:
            return None
    
    def _store_historical_prices(self):
        """Store historical egg prices for the last 30 days for all supported cities"""
        historical_data = self.historical_scraper.fetch_all_cities_historical()
        for city, prices in historical_data.items():
            for price_data in prices:
                self.db.store_egg_prices(
                    city,
                    {'rates': price_data['rates']},
                    date=price_data['date']
                )
    
    def close(self):
        """
        Close the database connection
        """
        self.db.close()


def main():
    agent = EggPriceAgentFireCrawlWithDB()
    print("=" * 60)
    print("🥚 Egg Price Agent (India) with Database 🥚")
    print("=" * 60)
    print("Type 'exit' to quit.")
    print("\nAsk me about egg prices, for example:")
    print("  - 'What is the price of eggs in Mumbai?'")
    print("  - 'Show me egg prices in Delhi'")
    print("  - 'Which cities do you have egg price data for?'")
    print("  - 'How much do 100 eggs cost in Bengaluru?'")
    print("  - 'What is the price of a tray in Chennai?'")
    print("  - 'Show me current egg rates'")
    print("\nYour queries will be stored in the MongoDB database.")
    
    while True:
        user_input = input("\nYour question: ")
        
        if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
            print("\nThank you for using the Egg Price Agent. Goodbye!")
            break
        
        response = agent.process_query(user_input)
        print(f"\nAgent: {response}")
    
    # Close the database connection when done
    agent.close()


if __name__ == "__main__":
    main()