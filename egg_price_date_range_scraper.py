from egg_price_historical_scraper import EggPriceHistoricalScraper
from egg_price_schema import EggPriceDatabase
from datetime import datetime, timedelta
import argparse

def scrape_date_range(start_date_str, end_date_str):
    """Scrape egg prices for all cities within the specified date range
    
    Args:
        start_date_str (str): Start date in DD-MM-YYYY format
        end_date_str (str): End date in DD-MM-YYYY format
    """
    try:
        # Parse dates
        start_date = datetime.strptime(start_date_str, '%d-%m-%Y').date()
        end_date = datetime.strptime(end_date_str, '%d-%m-%Y').date()
        
        if start_date > end_date:
            print("Error: Start date must be before end date")
            return
        
        # Initialize scraper and database
        scraper = EggPriceHistoricalScraper()
        db = EggPriceDatabase()
        
        # Get list of cities
        cities = scraper.city_urls.keys()
        
        print(f"Scraping egg prices from {start_date} to {end_date}")
        
        # Scrape data for each city
        for city in cities:
            print(f"\nProcessing {city.title()}...")
            historical_data = scraper.fetch_historical_prices(city)
            
            # Filter data for the specified date range
            for data in historical_data:
                if start_date <= data['date'] <= end_date:
                    # Check if data already exists
                    existing_data = db.get_prices_by_date(city, data['date'])
                    if existing_data:
                        print(f"Data already exists for {city} on {data['date']}")
                        continue
                    
                    # Store in database
                    result = db.store_egg_prices(
                        city=city,
                        price_data=data['rates'],
                        date=data['date']
                    )
                    if result:
                        print(f"Stored prices for {city} on {data['date']}")
                    else:
                        print(f"Failed to store prices for {city} on {data['date']}")
        
        print("\nScraping completed!")
        
    except ValueError as e:
        print(f"Error: Invalid date format. Please use DD-MM-YYYY format. {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")

def main():
    print("Welcome to Egg Price Date Range Scraper!")
    print("Please enter dates in DD-MM-YYYY format")
    
    while True:
        try:
            start_date = input("\nEnter start date (DD-MM-YYYY): ").strip()
            # Validate start date format
            datetime.strptime(start_date, '%d-%m-%Y')
            break
        except ValueError:
            print("Invalid date format! Please use DD-MM-YYYY format")
    
    while True:
        try:
            end_date = input("Enter end date (DD-MM-YYYY): ").strip()
            # Validate end date format
            datetime.strptime(end_date, '%d-%m-%Y')
            break
        except ValueError:
            print("Invalid date format! Please use DD-MM-YYYY format")
    
    scrape_date_range(start_date, end_date)

if __name__ == '__main__':
    main()