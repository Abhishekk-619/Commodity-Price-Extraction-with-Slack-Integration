from egg_price_historical_scraper import EggPriceHistoricalScraper
from egg_price_schema import EggPriceDatabase

def main():
    scraper = EggPriceHistoricalScraper()
    db = EggPriceDatabase()
    print('Fetching historical egg prices for all major cities...')
    historical_data = scraper.fetch_all_cities_historical()
    
    for city, prices in historical_data.items():
        print(f'\n{city.upper()} HISTORICAL PRICES:')
        if not prices:
            print('No historical data available')
            continue
            
        for data in prices:
            # Store data in MongoDB
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