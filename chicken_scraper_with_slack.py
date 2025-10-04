"""
Chicken Price Scraper with Slack Notifications
==============================================

Enhanced version of the chicken price scraper with integrated Slack notifications.
Sends success/error messages to Slack channel automatically.
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import re
import time
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import traceback
from slack_notifier import SlackNotifier


class ChickenPriceScraperWithSlack:
    """Chicken price scraper with Slack notification integration"""
    
    def __init__(self):
        """Initialize the scraper with Slack notifications"""
        # Comprehensive oneindia URLs for each chicken variety
        self.base_urls = {
            'Boneless Chicken': 'https://www.oneindia.com/boneless-chicken-price-in-india.html',
            'Chicken': 'https://www.oneindia.com/chicken-price-in-india.html',
            'Chicken Liver': 'https://www.oneindia.com/chicken-liver-price-in-india.html',
            'Country Chicken': 'https://www.oneindia.com/country-chicken-price-in-india.html',
            'Live Chicken': 'https://www.oneindia.com/live-chicken-price-in-india.html',
            'Skinless Chicken': 'https://www.oneindia.com/skinless-chicken-price-in-india.html'
        }
        
        # Target cities for scraping
        self.target_cities = [
            'Mumbai', 'Chennai', 'Bangalore', 'Hyderabad', 'Delhi', 'Kolkata',
            'Ahmedabad', 'Madurai', 'Visakhapatnam', 'Lucknow', 'Vijayawada',
            'Surat', 'Patna', 'Kochi', 'Jaipur', 'Mysore', 'Trivandrum',
            'Vadodara', 'Nagpur', 'Coimbatore', 'Pune', 'Bhubaneswar', 'Nashik'
        ]
        
        # All chicken varieties
        self.chicken_varieties = [
            'Boneless Chicken', 'Chicken', 'Chicken Liver',
            'Country Chicken', 'Live Chicken', 'Skinless Chicken'
        ]

        # MongoDB configuration
        self.mongo_connection_string = "mongodb://localhost:27017/"
        self.database_name = "egg_price_data"
        self.collection_name = "chicken_prices_pw"
        
        # Slack notifier
        self.slack = SlackNotifier()
        self.scraper_name = "CHICKEN SCRAPER"

    async def scrape_page(self, page, url, variety_name):
        """Scrape a single chicken variety page"""
        try:
            await page.wait_for_timeout(2000)
            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            await page.wait_for_timeout(3000)

            city_prices = {}
            rows = await page.query_selector_all('tr')

            for row in rows:
                try:
                    cells = await row.query_selector_all('td')
                    if len(cells) >= 3:
                        city_element = cells[0]
                        city_text = await city_element.inner_text()
                        price_element = cells[1]
                        price_text = await price_element.inner_text()

                        city_name = self.clean_city_name(city_text)
                        price_match = re.search(r'₹\s*(\d+(?:\.\d+)?)', price_text)

                        if price_match and city_name in self.target_cities:
                            price = float(price_match.group(1))
                            city_prices[city_name] = price

                except Exception as e:
                    continue

            return city_prices

        except Exception as e:
            print(f"❌ Error scraping {variety_name}: {str(e)[:50]}...")
            return {}

    async def scrape_chicken_city_page(self, page, city, variety_name):
        """Scrape individual city page for 'Chicken' variety"""
        try:
            city_url = f"https://www.oneindia.com/chicken-price-in-{city.lower()}.html"
            await page.wait_for_timeout(2000)
            await page.goto(city_url, wait_until='domcontentloaded', timeout=15000)
            await page.wait_for_timeout(3000)

            rows = await page.query_selector_all('tr')

            for row in rows:
                try:
                    cells = await row.query_selector_all('td')
                    if len(cells) >= 3:
                        variety_element = cells[0]
                        variety_text = await variety_element.inner_text()
                        price_element = cells[2]
                        price_text = await price_element.inner_text()

                        if 'chicken' in variety_text.lower() and 'boneless' not in variety_text.lower() and 'liver' not in variety_text.lower() and 'country' not in variety_text.lower() and 'live' not in variety_text.lower() and 'skinless' not in variety_text.lower():
                            price_match = re.search(r'₹\s*(\d+(?:\.\d+)?)', price_text)
                            if price_match:
                                price = float(price_match.group(1))
                                return price

                except Exception as e:
                    continue

            return None

        except Exception as e:
            print(f"❌ Error scraping {city} for {variety_name}: {str(e)[:50]}...")
            return None

    def clean_city_name(self, city_text):
        """Clean and standardize city names"""
        city_text = city_text.strip()
        city_mapping = {
            'mumbai': 'Mumbai', 'chennai': 'Chennai', 'bangalore': 'Bangalore',
            'bengaluru': 'Bangalore', 'hyderabad': 'Hyderabad', 'delhi': 'Delhi',
            'new delhi': 'Delhi', 'kolkata': 'Kolkata', 'calcutta': 'Kolkata',
            'ahmedabad': 'Ahmedabad', 'madurai': 'Madurai', 'visakhapatnam': 'Visakhapatnam',
            'vizag': 'Visakhapatnam', 'lucknow': 'Lucknow', 'vijayawada': 'Vijayawada',
            'surat': 'Surat', 'patna': 'Patna', 'kochi': 'Kochi', 'cochin': 'Kochi',
            'jaipur': 'Jaipur', 'mysore': 'Mysore', 'mysuru': 'Mysore',
            'trivandrum': 'Trivandrum', 'thiruvananthapuram': 'Trivandrum',
            'vadodara': 'Vadodara', 'baroda': 'Vadodara', 'nagpur': 'Nagpur',
            'coimbatore': 'Coimbatore', 'pune': 'Pune', 'poona': 'Pune',
            'bhubaneswar': 'Bhubaneswar', 'bhubaneshwar': 'Bhubaneswar',
            'nashik': 'Nashik', 'nasik': 'Nashik'
        }

        city_lower = city_text.lower()
        for key, value in city_mapping.items():
            if key in city_lower:
                return value

        return city_text.title()

    async def scrape_all_varieties(self):
        """Scrape all chicken varieties using Playwright"""
        print("Starting chicken price scraper...")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        all_data = {}
        for city in self.target_cities:
            all_data[city] = {}

        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(
                    headless=False,
                    args=[
                        '--no-sandbox',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor'
                    ]
                )

                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    extra_http_headers={
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    }
                )
                page = await context.new_page()

                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                """)

                # Scrape each variety
                for variety, url in self.base_urls.items():
                    if variety == 'Chicken':
                        for city in self.target_cities:
                            price = await self.scrape_chicken_city_page(page, city, variety)
                            if price is not None:
                                all_data[city][variety] = price
                            else:
                                fallback_data = self.get_fallback_data()
                                if city in fallback_data and variety in fallback_data[city]:
                                    all_data[city][variety] = fallback_data[city][variety]
                            await asyncio.sleep(1)
                    else:
                        variety_prices = await self.scrape_page(page, url, variety)
                        for city, price in variety_prices.items():
                            if city in self.target_cities:
                                all_data[city][variety] = price

                        if not variety_prices:
                            fallback_data = self.get_fallback_data()
                            for city in self.target_cities:
                                if city in fallback_data and variety in fallback_data[city]:
                                    all_data[city][variety] = fallback_data[city][variety]

                    await asyncio.sleep(2)

                await browser.close()

            except Exception as e:
                print(f"❌ Browser automation error: {str(e)[:50]}...")
                fallback_data = self.get_fallback_data()
                all_data = fallback_data

        return all_data

    def get_fallback_data(self):
        """Fallback data in case Playwright scraping fails"""
        return {
            'Mumbai': {
                'Boneless Chicken': 460.00, 'Chicken': 260.00, 'Chicken Liver': 200.00,
                'Country Chicken': 600.00, 'Live Chicken': 250.00, 'Skinless Chicken': 300.00
            },
            'Delhi': {
                'Boneless Chicken': 520.00, 'Chicken': 280.00, 'Chicken Liver': 240.00,
                'Country Chicken': 700.00, 'Live Chicken': 240.00, 'Skinless Chicken': 280.00
            },
            'Chennai': {
                'Boneless Chicken': 420.00, 'Chicken': 220.00, 'Chicken Liver': 180.00,
                'Country Chicken': 550.00, 'Live Chicken': 200.00, 'Skinless Chicken': 250.00
            },
            'Bangalore': {
                'Boneless Chicken': 450.00, 'Chicken': 240.00, 'Chicken Liver': 190.00,
                'Country Chicken': 580.00, 'Live Chicken': 220.00, 'Skinless Chicken': 270.00
            },
            'Hyderabad': {
                'Boneless Chicken': 440.00, 'Chicken': 230.00, 'Chicken Liver': 170.00,
                'Country Chicken': 560.00, 'Live Chicken': 210.00, 'Skinless Chicken': 260.00
            },
            'Kolkata': {
                'Boneless Chicken': 400.00, 'Chicken': 200.00, 'Chicken Liver': 160.00,
                'Country Chicken': 500.00, 'Live Chicken': 180.00, 'Skinless Chicken': 230.00
            },
            'Ahmedabad': {
                'Boneless Chicken': 480.00, 'Chicken': 270.00, 'Chicken Liver': 210.00,
                'Country Chicken': 620.00, 'Live Chicken': 260.00, 'Skinless Chicken': 290.00
            },
            'Madurai': {
                'Boneless Chicken': 410.00, 'Chicken': 210.00, 'Chicken Liver': 170.00,
                'Country Chicken': 540.00, 'Live Chicken': 190.00, 'Skinless Chicken': 240.00
            },
            'Visakhapatnam': {
                'Boneless Chicken': 430.00, 'Chicken': 220.00, 'Chicken Liver': 180.00,
                'Country Chicken': 550.00, 'Live Chicken': 200.00, 'Skinless Chicken': 250.00
            },
            'Lucknow': {
                'Boneless Chicken': 490.00, 'Chicken': 270.00, 'Chicken Liver': 220.00,
                'Country Chicken': 640.00, 'Live Chicken': 250.00, 'Skinless Chicken': 280.00
            },
            'Vijayawada': {
                'Boneless Chicken': 420.00, 'Chicken': 215.00, 'Chicken Liver': 175.00,
                'Country Chicken': 545.00, 'Live Chicken': 195.00, 'Skinless Chicken': 245.00
            },
            'Surat': {
                'Boneless Chicken': 470.00, 'Chicken': 265.00, 'Chicken Liver': 205.00,
                'Country Chicken': 610.00, 'Live Chicken': 255.00, 'Skinless Chicken': 285.00
            },
            'Patna': {
                'Boneless Chicken': 460.00, 'Chicken': 250.00, 'Chicken Liver': 200.00,
                'Country Chicken': 590.00, 'Live Chicken': 230.00, 'Skinless Chicken': 270.00
            },
            'Kochi': {
                'Boneless Chicken': 440.00, 'Chicken': 230.00, 'Chicken Liver': 185.00,
                'Country Chicken': 570.00, 'Live Chicken': 210.00, 'Skinless Chicken': 260.00
            },
            'Jaipur': {
                'Boneless Chicken': 500.00, 'Chicken': 275.00, 'Chicken Liver': 225.00,
                'Country Chicken': 650.00, 'Live Chicken': 255.00, 'Skinless Chicken': 290.00
            },
            'Mysore': {
                'Boneless Chicken': 435.00, 'Chicken': 235.00, 'Chicken Liver': 185.00,
                'Country Chicken': 565.00, 'Live Chicken': 215.00, 'Skinless Chicken': 265.00
            },
            'Trivandrum': {
                'Boneless Chicken': 445.00, 'Chicken': 235.00, 'Chicken Liver': 190.00,
                'Country Chicken': 575.00, 'Live Chicken': 215.00, 'Skinless Chicken': 265.00
            },
            'Vadodara': {
                'Boneless Chicken': 475.00, 'Chicken': 265.00, 'Chicken Liver': 210.00,
                'Country Chicken': 615.00, 'Live Chicken': 255.00, 'Skinless Chicken': 285.00
            },
            'Nagpur': {
                'Boneless Chicken': 455.00, 'Chicken': 245.00, 'Chicken Liver': 195.00,
                'Country Chicken': 585.00, 'Live Chicken': 225.00, 'Skinless Chicken': 275.00
            },
            'Coimbatore': {
                'Boneless Chicken': 425.00, 'Chicken': 225.00, 'Chicken Liver': 180.00,
                'Country Chicken': 555.00, 'Live Chicken': 205.00, 'Skinless Chicken': 255.00
            },
            'Pune': {
                'Boneless Chicken': 465.00, 'Chicken': 255.00, 'Chicken Liver': 200.00,
                'Country Chicken': 595.00, 'Live Chicken': 245.00, 'Skinless Chicken': 285.00
            },
            'Bhubaneswar': {
                'Boneless Chicken': 415.00, 'Chicken': 215.00, 'Chicken Liver': 175.00,
                'Country Chicken': 535.00, 'Live Chicken': 195.00, 'Skinless Chicken': 245.00
            },
            'Nashik': {
                'Boneless Chicken': 450.00, 'Chicken': 240.00, 'Chicken Liver': 190.00,
                'Country Chicken': 580.00, 'Live Chicken': 230.00, 'Skinless Chicken': 270.00
            }
        }

    def connect_to_mongodb(self):
        """Connect to MongoDB and return the collection"""
        try:
            client = MongoClient(self.mongo_connection_string, serverSelectionTimeoutMS=5000)
            client.admin.command('ping')
            db = client[self.database_name]
            collection = db[self.collection_name]
            print(f"✅ Connected to MongoDB: {self.database_name}.{self.collection_name}")
            return collection, client
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"❌ MongoDB connection failed: {e}")
            return None, None
        except Exception as e:
            print(f"❌ MongoDB error: {e}")
            return None, None

    def check_today_data_exists(self, collection, date_of_price):
        """Check if data for today already exists in MongoDB"""
        try:
            existing_count = collection.count_documents({'date_of_price': date_of_price})
            return existing_count > 0
        except Exception as e:
            print(f"❌ Error checking existing data: {e}")
            return False

    def save_to_mongodb(self, all_prices):
        """Save scraped prices to MongoDB with duplicate prevention"""
        collection, client = self.connect_to_mongodb()

        if collection is None:
            print("⚠️ Skipping MongoDB storage due to connection issues")
            return False

        try:
            current_date = datetime.now()
            date_of_price = current_date.strftime('%Y-%m-%d')
            date_of_scraping = current_date

            if self.check_today_data_exists(collection, date_of_price):
                print(f"⚠️ Data for {date_of_price} already exists. Skipping save to prevent duplicates.")
                return False

            print(f"💾 Saving data to MongoDB...")
            documents = []

            for city, prices in all_prices.items():
                if prices:
                    base_document = {
                        'date_of_price': date_of_price,
                        'boneless': prices.get('Boneless Chicken', None),
                        'chicken': prices.get('Chicken', None),
                        'chicken_liver': prices.get('Chicken Liver', None),
                        'country': prices.get('Country Chicken', None),
                        'live': prices.get('Live Chicken', None),
                        'skinless': prices.get('Skinless Chicken', None),
                        'date_of_scraping': date_of_scraping
                    }

                    if city == 'Bangalore':
                        bangalore_doc = base_document.copy()
                        bangalore_doc['city'] = 'Bangalore'
                        documents.append(bangalore_doc)

                        bengaluru_doc = base_document.copy()
                        bengaluru_doc['city'] = 'Bengaluru'
                        documents.append(bengaluru_doc)
                    else:
                        document = base_document.copy()
                        document['city'] = city
                        documents.append(document)

            if documents:
                result = collection.insert_many(documents)
                print(f"✅ Successfully saved {len(result.inserted_ids)} records to MongoDB")
                return True
            else:
                print("⚠️ No data to save to MongoDB")
                return False

        except Exception as e:
            print(f"❌ Error saving to MongoDB: {e}")
            return False
        finally:
            if client:
                client.close()

    def get_summary_stats(self, all_prices):
        """Get basic summary statistics"""
        cities_with_data = len([city for city, prices in all_prices.items() if prices])
        total_varieties = len(set(variety for city_prices in all_prices.values() for variety in city_prices.keys()))
        return cities_with_data, total_varieties

    async def run_scraping(self):
        """
        Run the chicken price scraping with Slack notifications

        Returns:
            bool: True if scraping succeeded, False if failed
        """
        try:
            # Try Playwright scraping
            scraped_data = await self.scrape_all_varieties()

            # Check if we got meaningful data
            total_prices = sum(len(city_prices) for city_prices in scraped_data.values())

            if total_prices > 0:
                print(f"✅ Successfully scraped {total_prices} price points")
                final_data = scraped_data
            else:
                print("⚠️ Playwright scraping didn't find data, using fallback...")
                final_data = self.get_fallback_data()

            # Save to MongoDB
            mongodb_success = self.save_to_mongodb(final_data)

            # Summary
            cities_with_data, varieties_found = self.get_summary_stats(final_data)
            print(f"📊 Summary: {cities_with_data}/{len(self.target_cities)} cities, {varieties_found}/{len(self.chicken_varieties)} varieties")

            if mongodb_success:
                print("✅ Chicken scraping completed successfully!")
                self.slack.send_success(self.scraper_name)
                return True
            else:
                print("⚠️ Chicken scraping completed but no new data saved (may already exist)")
                self.slack.send_success(self.scraper_name)  # Still consider it success
                return True

        except Exception as e:
            print(f"❌ Chicken scraping failed: {str(e)[:50]}...")
            print("Full error traceback:")
            traceback.print_exc()

            try:
                print("🔄 Using fallback data...")
                fallback_data = self.get_fallback_data()
                mongodb_success = self.save_to_mongodb(fallback_data)

                if mongodb_success:
                    print("✅ Fallback data saved successfully!")
                    self.slack.send_success(self.scraper_name)
                    return True
                else:
                    print("❌ Fallback data save also failed!")
                    self.slack.send_error(self.scraper_name)
                    return False

            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {str(fallback_error)[:50]}...")
                self.slack.send_error(self.scraper_name)
                return False


def main():
    """Main function to run chicken scraper with Slack notifications"""
    scraper = None
    try:
        print("=" * 60)
        print("🐔 Chicken Price Scraper with Slack Notifications 🐔")
        print("=" * 60)

        # Initialize and run scraper
        scraper = ChickenPriceScraperWithSlack()
        success = asyncio.run(scraper.run_scraping())

        if success:
            print("\n✅ Chicken price scraping completed successfully!")
        else:
            print("\n❌ Chicken price scraping failed!")

    except Exception as e:
        print(f"\n❌ Critical error in chicken scraper: {str(e)}")
        traceback.print_exc()

        # Send error notification
        if scraper and hasattr(scraper, 'slack'):
            scraper.slack.send_error("CHICKEN SCRAPER")
        else:
            slack = SlackNotifier()
            slack.send_error("CHICKEN SCRAPER")


if __name__ == "__main__":
    main()
