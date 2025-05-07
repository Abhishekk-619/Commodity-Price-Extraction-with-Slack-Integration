from egg_price_historical_scraper import EggPriceHistoricalScraper
from egg_price_schema import EggPriceDatabase

def main():
    scraper = EggPriceHistoricalScraper()
    db = EggPriceDatabase()
    print('Fetching historical egg prices for all major cities...')
    
    # Get today's date to check if we already have entries for today
    from datetime import datetime, timedelta
    today = datetime.now().date()
    
    # Calculate the date range for the past 30 days
    past_30_days = [(today - timedelta(days=i)) for i in range(30)]
    
    # Get existing entries for today to avoid duplicates
    existing_entries = {}
    try:
        # Get latest prices for all cities
        latest_prices = db.get_latest_prices()
        for entry in latest_prices:
            # For aggregation result structure
            if '_id' in entry and 'latest_price' in entry:
                city = entry['_id']
                date = entry['latest_price'].get('date')
                if date and date.date() == today:
                    existing_entries[city] = today
                    print(f"Found existing entry for {city} on {today}")
            # For direct query result structure
            elif 'city' in entry and 'date' in entry:
                city = entry['city']
                date = entry['date']
                if date and date.date() == today:
                    existing_entries[city] = today
                    print(f"Found existing entry for {city} on {today}")
    except Exception as e:
        print(f"Error checking existing entries: {e}")
    
    # Check for missing data in the past 30 days
    cities = ['mumbai', 'delhi', 'bengaluru', 'chennai', 'hyderabad', 'kolkata']
    missing_data = {}
    
    # Get all existing entries for the past 30 days
    for city in cities:
        try:
            city_entries = db.egg_prices.find({'city': city, 'date': {'$gte': datetime.combine(past_30_days[-1], datetime.min.time())}})
            existing_dates = {entry['date'].date() for entry in city_entries}
            missing_dates = [date for date in past_30_days if date not in existing_dates]
            if missing_dates:
                missing_data[city] = missing_dates
        except Exception as e:
            print(f"Error checking historical data for {city}: {e}")
    
    if not missing_data:
        print("\nAll cities have complete data for the past 30 days.")
        db.close()
        return
    
    print("\nFetching historical data for cities with missing dates:")
    for city, dates in missing_data.items():
        print(f"{city}: Missing {len(dates)} days")
    
    historical_data = scraper.fetch_all_cities_historical()
    
    for city, prices in historical_data.items():
        if city not in missing_data:
            print(f'\n{city.upper()}: No missing data, skipping')
            continue
            
        print(f'\n{city.upper()} HISTORICAL PRICES:')
        if not prices:
            print('No historical data available')
            continue
            
        for data in prices:
            # Only store data for missing dates
            if data['date'] in missing_data.get(city, []):
                # Store historical data in MongoDB
                db.store_egg_prices(city, {'rates': data['rates']}, date=data['date'])
                
                # Print the data
                print(f"Date: {data['date']} - Single Egg: ₹{data['rates']['single_egg']:.2f}")
                print(f"Tray (30): ₹{data['rates']['tray']:.2f}")
                print(f"100 Eggs: ₹{data['rates']['hundred_eggs']:.2f}")
                print(f"Box (210): ₹{data['rates']['box']:.2f}")
                print('-' * 50)
    
    # Close the database connection
    db.close()

if __name__ == '__main__':
    main()