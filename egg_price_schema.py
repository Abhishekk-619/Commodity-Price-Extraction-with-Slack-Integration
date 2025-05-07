from pymongo import MongoClient
from datetime import datetime

class EggPriceDatabase:
    def __init__(self, connection_string="mongodb://localhost:27017/", db_name="egg_price_data"):
        try:
            self.client = MongoClient(connection_string)
            self.db = self.client[db_name]
            self.egg_prices = self.db.egg_prices
            # Test connection
            self.client.admin.command('ping')
            print("Connected successfully to MongoDB")
        except Exception as e:
            print(f"MongoDB connection error: {e}")
            raise
    
    def store_egg_prices(self, city, price_data, date=None):
        """
        Store egg prices for a city with timestamp
        
        Args:
            city (str): City name
            price_data (dict): Dictionary containing egg prices
            date (datetime.date, optional): The date for historical prices
        """
        try:
            # Extract rates from price data
            rates = self._extract_rates(price_data)
            
            # Only store if we have valid rates
            if any(rate is not None for rate in rates.values()):
                # Set current timestamp for when the data is being stored
                current_timestamp = datetime.utcnow()
                
                # Handle date conversion with proper validation
                try:
                    if date:
                        if hasattr(date, 'hour'):  # Already a datetime object
                            historical_date = date
                        else:  # Convert date to datetime at midnight
                            historical_date = datetime.combine(date, datetime.min.time())
                    else:
                        historical_date = current_timestamp
                except (AttributeError, TypeError):
                    historical_date = current_timestamp
                
                document = {
                    'city': city.lower(),  # Normalize city names
                    'rates': rates,
                    'timestamp': current_timestamp,  # When the data was stored
                    'date': historical_date,  # When the prices were actually recorded
                    'query_text': str(price_data)  # Store original query for reference
                }
                
                # Upsert the document based on city and date
                result = self.egg_prices.update_one(
                    {
                        'city': city.lower(),
                        'date': historical_date
                    },
                    {'$set': document},
                    upsert=True
                )
                
                if result.upserted_id:
                    print(f"Created new price entry for {city} on {document['date']}")
                else:
                    print(f"Updated existing price entry for {city} on {document['date']}")
                    
                return result.upserted_id or result.modified_count
            else:
                print(f"No valid rates found for {city}")
                return None
            
        except Exception as e:
            print(f"Error storing egg prices: {e}")
            return None
    
    def _extract_rates(self, response):
        """
        Extract the four types of rates from agent response
        
        Args:
            response (str|dict): Price data in string or dictionary format
            
        Returns:
            dict: Standardized rates with numeric values
        """
        rates = {
            'single_egg': {'price': None, 'quantity': 1},
            'tray': {'price': None, 'quantity': 30},
            'hundred_eggs': {'price': None, 'quantity': 100},
            'box': {'price': None, 'quantity': 210}
        }
        
        try:
            if isinstance(response, str):
                lines = response.split('\n')
            elif isinstance(response, dict):
                # If response is already a dictionary, process it directly
                lines = [f"- {k}: {v}" for k, v in response.items()]
            else:
                return rates

            for line in lines:
                if ':' in line and (line.strip().startswith('-') or isinstance(response, dict)):
                    parts = line.strip().lstrip('- ').split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip().lower()
                        value = parts[1].strip()
                        
                        try:
                            # Extract numeric value, handling different formats
                            if '₹' in value:
                                # Remove rupee symbol and any whitespace
                                price_str = value.replace('₹', '').strip()
                                # Remove any other non-numeric characters except decimal point
                                price_str = ''.join(c for c in price_str if c.isdigit() or c == '.')
                                # Ensure the string is not empty and doesn't end with a decimal point
                                if price_str and not price_str.endswith('.'):
                                    try:
                                        price = float(price_str)
                                        # Map to standardized rate keys with price and quantity
                                        if any(term in key for term in ['single', '1 egg']):
                                            rates['single_egg']['price'] = price
                                        elif any(term in key for term in ['tray', '30']):
                                            rates['tray']['price'] = price
                                        elif '100' in key:
                                            rates['hundred_eggs']['price'] = price
                                        elif any(term in key for term in ['box', '210']):
                                            rates['box']['price'] = price
                                    except ValueError:
                                        # Skip invalid numeric values
                                        continue
                        except ValueError:
                            continue
            
            return rates
            
        except Exception as e:
            print(f"Error extracting rates: {e}")
            return rates
    
    def get_latest_prices(self, city=None):
        """
        Get the latest egg prices for a city or all cities
        
        Args:
            city (str, optional): Name of the city. If None, returns all cities.
        """
        try:
            if city:
                # Get latest price for specific city
                result = self.egg_prices.find({'city': city}).sort('timestamp', -1).limit(1)
            else:
                # Get latest prices for all cities
                pipeline = [
                    {'$sort': {'timestamp': -1}},
                    {'$group': {
                        '_id': '$city',
                        'latest_price': {'$first': '$$ROOT'}
                    }}
                ]
                result = self.egg_prices.aggregate(pipeline)
            
            return list(result)
            
        except Exception as e:
            print(f"Error retrieving egg prices: {e}")
            return []
    
    def close(self):
        """Close the MongoDB connection"""
        if hasattr(self, 'client'):
            self.client.close()
            print("MongoDB connection closed")