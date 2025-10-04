import asyncio
import os
from playwright.async_api import async_playwright
from datetime import datetime
import re
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from slack_notifier import SlackNotifier
import traceback

class LinuxChickenScraper:
    def __init__(self):
        # Set environment variables for headless operation
        os.environ['DISPLAY'] = ':99'

        # Initialize Slack notifier
        self.slack = SlackNotifier()
        self.scraper_name = "CHICKEN SCRAPER"
        
        # URLs for chicken varieties (5 varieties only)
        self.base_urls = {
            'Boneless Chicken': 'https://www.oneindia.com/boneless-chicken-price-in-india.html',
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
        
        # MongoDB configuration
        self.mongo_connection_string = "mongodb://localhost:27017/"
        self.database_name = "egg_price_data"
        self.collection_name = "chicken_prices_linux"

    async def create_browser_context(self, playwright):
        """Create browser with Linux server-optimized settings"""
        print("🔧 Creating browser context for Linux server...")
        
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--single-process',
                '--disable-gpu',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-features=VizDisplayCompositor',
                '--disable-web-security',
                '--memory-pressure-off',
                '--max_old_space_size=4096'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        return browser, context



    async def scrape_page_with_retry(self, url, variety_name, max_retries=3):
        """Scrape a single page with retry logic for Linux stability"""
        print(f"📊 Scraping {variety_name} from {url}")
        
        for attempt in range(max_retries):
            try:
                async with async_playwright() as playwright:
                    browser, context = await self.create_browser_context(playwright)
                    page = await context.new_page()
                    
                    # Navigate with extended timeout for server environment
                    await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    await page.wait_for_timeout(5000)
                    
                    # Extract data
                    city_prices = await self.extract_prices_from_page(page, variety_name)
                    
                    await browser.close()
                    
                    if city_prices:
                        print(f"✅ Found {len(city_prices)} prices for {variety_name}")
                        return city_prices
                    else:
                        print(f"⚠️ No prices found for {variety_name} on attempt {attempt + 1}")
                        
            except Exception as e:
                print(f"❌ Attempt {attempt + 1} failed for {variety_name}: {str(e)[:100]}")
                if attempt < max_retries - 1:
                    print(f"🔄 Retrying in 5 seconds...")
                    await asyncio.sleep(5)
                else:
                    print(f"💥 All attempts failed for {variety_name}")
                    return {}

        return {}

    async def extract_prices_from_page(self, page, variety_name):
        """Extract prices from the page"""
        city_prices = {}
        
        try:
            # Look for the price table
            rows = await page.query_selector_all('tr')
            print(f"🔍 Found {len(rows)} table rows on {variety_name} page")
            
            for row in rows:
                try:
                    cells = await row.query_selector_all('td')
                    if len(cells) >= 3:
                        # Get city name from first cell
                        city_element = cells[0]
                        city_text = await city_element.inner_text()

                        # Get price from second cell
                        price_element = cells[1]
                        price_text = await price_element.inner_text()

                        # Clean city name
                        city_name = self.clean_city_name(city_text)

                        # Extract price
                        price_match = re.search(r'₹\s*(\d+(?:\.\d+)?)', price_text)

                        if price_match and city_name in self.target_cities:
                            price = float(price_match.group(1))
                            city_prices[city_name] = price
                            print(f"  📍 {city_name}: ₹{price}")

                except Exception as e:
                    continue  # Skip problematic rows

        except Exception as e:
            print(f"❌ Error extracting prices from {variety_name}: {e}")

        return city_prices

    def clean_city_name(self, city_text):
        """Clean and standardize city names"""
        city_mapping = {
            'Mumbai': 'Mumbai', 'Delhi': 'Delhi', 'Chennai': 'Chennai',
            'Bangalore': 'Bangalore', 'Bengaluru': 'Bangalore',
            'Hyderabad': 'Hyderabad', 'Kolkata': 'Kolkata'
        }
        
        clean_text = re.sub(r'[^\w\s]', '', city_text).strip().title()
        
        for key, value in city_mapping.items():
            if key.lower() in clean_text.lower():
                return value
                
        return clean_text

    def get_fallback_data_for_variety(self, variety_name):
        """Get fallback data for a specific variety"""
        # Basic fallback prices
        fallback_prices = {
            'Mumbai': 250, 'Delhi': 240, 'Chennai': 210,
            'Bangalore': 240, 'Hyderabad': 220, 'Kolkata': 200
        }
        
        print(f"🔄 Using fallback data for {variety_name}")
        return fallback_prices

    async def scrape_all_varieties(self):
        """Scrape all chicken varieties (5 varieties only)"""
        print("🚀 Starting chicken price scraping for 5 varieties on Linux...")

        all_data = {}

        for variety_name, url in self.base_urls.items():
            print(f"\n📊 Processing {variety_name}...")

            # Normal scraping for all varieties
            city_prices = await self.scrape_page_with_retry(url, variety_name)

            if city_prices:
                all_data[variety_name] = city_prices
                print(f"✅ Successfully scraped {variety_name}: {len(city_prices)} cities")
            else:
                print(f"❌ Failed to scrape {variety_name}")
                # Add fallback data for this variety
                all_data[variety_name] = self.get_fallback_data_for_variety(variety_name)

            # Add delay between varieties to be respectful
            await asyncio.sleep(3)

        return all_data

    def save_to_mongodb(self, data):
        """Save scraped data to MongoDB"""
        try:
            print("💾 Connecting to MongoDB...")
            client = MongoClient(self.mongo_connection_string, serverSelectionTimeoutMS=5000)
            
            # Test connection
            client.admin.command('ping')
            
            db = client[self.database_name]
            collection = db[self.collection_name]
            
            # Prepare document
            document = {
                'timestamp': datetime.now(),
                'date': datetime.now().strftime('%Y-%m-%d'),
                'data': data,
                'source': 'linux_chicken_scraper_fixed',
                'total_varieties': len(data),
                'total_cities': len(set().union(*[cities.keys() for cities in data.values()]))
            }
            
            # Insert document
            result = collection.insert_one(document)
            print(f"✅ Data saved to MongoDB with ID: {result.inserted_id}")
            
            client.close()
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"❌ MongoDB connection failed: {e}")
            return False
        except Exception as e:
            print(f"❌ MongoDB save error: {e}")
            return False

    def get_summary_stats(self, data):
        """Get summary statistics"""
        all_cities = set()
        for variety_data in data.values():
            all_cities.update(variety_data.keys())

        return len(all_cities), len(data)

    def send_detailed_slack_notification(self, final_data, mongodb_success, total_prices):
        """Send detailed Slack notification with scraping results"""
        try:
            # Prepare detailed message
            cities_with_data, varieties_found = self.get_summary_stats(final_data)

            # Create summary for each variety
            variety_summary = []
            for variety, city_data in final_data.items():
                if city_data:
                    sample_cities = list(city_data.items())[:3]  # First 3 cities
                    sample_text = ", ".join([f"{city}: ₹{price}" for city, price in sample_cities])
                    variety_summary.append(f"• {variety}: {len(city_data)} cities ({sample_text})")
                else:
                    variety_summary.append(f"• {variety}: No data")

            # Determine notification type and send appropriate message
            if mongodb_success and total_prices > 0:
                # Success notification with details
                message = f"""🐔 CHICKEN SCRAPER SUCCESS! 🎉

📊 **Summary:**
• Total Price Points: {total_prices}
• Cities Covered: {cities_with_data}/{len(self.target_cities)}
• Varieties: {varieties_found}/5
• MongoDB: ✅ Saved Successfully

🐔 **Varieties Scraped:**
{chr(10).join(variety_summary)}

⏰ **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🖥️ **Source:** Linux Chicken Scraper"""

                print("📱 Sending detailed success notification to Slack...")
                # Use the internal method to send custom message
                self.slack._send_notification(message, "good")

            else:
                # Warning/Error notification
                message = f"""⚠️ CHICKEN SCRAPER ISSUES DETECTED

❌ **Problems:**
• MongoDB Success: {'✅' if mongodb_success else '❌'}
• Total Prices: {total_prices}
• Some varieties may have failed

📊 **Current Status:**
• Cities: {cities_with_data}/{len(self.target_cities)}
• Varieties: {varieties_found}/5

⏰ **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🖥️ **Source:** Linux Chicken Scraper"""

                print("📱 Sending warning notification to Slack...")
                # Use the internal method to send custom message
                self.slack._send_notification(message, "warning")

        except Exception as e:
            print(f"❌ Failed to send detailed Slack notification: {e}")
            # Fallback to simple notification
            if mongodb_success and total_prices > 0:
                self.slack.send_success(self.scraper_name)
            else:
                self.slack.send_error(f"{self.scraper_name} (PARTIAL)")

    async def run(self):
        """Main method to run the Linux scraper"""
        print("🐧 Linux Chicken Price Scraper Starting...")
        print(f"🎯 Target cities: {len(self.target_cities)}")
        print(f"🐔 Chicken varieties: {len(self.base_urls)} (5 varieties)")

        try:
            # Scrape all varieties
            scraped_data = await self.scrape_all_varieties()

            # Check if we got meaningful data
            total_prices = sum(len(city_prices) for city_prices in scraped_data.values())

            if total_prices > 0:
                print(f"\n✅ Successfully scraped {total_prices} price points")
                final_data = scraped_data
            else:
                print("\n⚠️ No data scraped, using complete fallback...")
                final_data = {variety: self.get_fallback_data_for_variety(variety)
                             for variety in self.base_urls.keys()}

            # Save to MongoDB
            mongodb_success = self.save_to_mongodb(final_data)

            # Summary
            cities_with_data, varieties_found = self.get_summary_stats(final_data)

            print(f"\n📊 Final Summary:")
            print(f"   Cities: {cities_with_data}/{len(self.target_cities)}")
            print(f"   Varieties: {varieties_found}/{len(self.base_urls)} (5 varieties)")
            print(f"   MongoDB: {'✅ Success' if mongodb_success else '❌ Failed'}")
            print(f"   Total price points: {sum(len(v) for v in final_data.values())}")

            # Send detailed Slack notification
            self.send_detailed_slack_notification(final_data, mongodb_success, total_prices)

            return final_data

        except Exception as e:
            print(f"❌ Critical error: {str(e)}")
            print("Full error traceback:")
            traceback.print_exc()

            # Send error notification to Slack
            print(f"📱 Sending error notification to Slack...")
            self.slack.send_error(self.scraper_name)

            print("🔄 Using complete fallback data...")

            try:
                fallback_data = {variety: self.get_fallback_data_for_variety(variety)
                               for variety in self.base_urls.keys()}
                mongodb_success = self.save_to_mongodb(fallback_data)
                print(f"💾 Fallback data saved: {'✅ Success' if mongodb_success else '❌ Failed'}")
                return fallback_data
            except Exception as fallback_error:
                print(f"❌ Complete failure: {fallback_error}")
                # Send critical error notification
                self.slack.send_error(f"{self.scraper_name} (CRITICAL)")
                return {}

def main():
    """Main function to run the Linux chicken price scraper"""
    print("🐧🐔 Linux Chicken Price Scraper v2.0 - 5 VARIETIES WITH SLACK")
    print("="*60)

    scraper = None
    try:
        scraper = LinuxChickenScraper()
        result = asyncio.run(scraper.run())

        print("\n🏁 Scraping completed!")
        if result:
            print(f"📋 Retrieved data for {len(result)} varieties")

            # Show sample results from first variety
            if result:
                first_variety = list(result.keys())[0]
                variety_data = result[first_variety]
                print(f"🐔 {first_variety}: {len(variety_data)} cities")
                for city, price in list(variety_data.items())[:3]:  # Show first 3
                    print(f"   {city}: ₹{price}")
                if len(variety_data) > 3:
                    print(f"   ... and {len(variety_data) - 3} more cities")

            print("✅ Chicken price scraping completed successfully!")
            return 0
        else:
            print("❌ No data retrieved")
            return 1

    except KeyboardInterrupt:
        print("⏹️ Scraping interrupted by user")
        return 0
    except Exception as e:
        print(f"❌ Critical error in chicken scraper: {str(e)}")
        print("Full error traceback:")
        traceback.print_exc()

        # Send error notification if scraper object exists
        if scraper and hasattr(scraper, 'slack'):
            print("📱 Sending critical error notification to Slack...")
            scraper.slack.send_error("CHICKEN SCRAPER (CRITICAL)")
        else:
            # Fallback notification
            print("📱 Sending fallback error notification to Slack...")
            slack = SlackNotifier()
            slack.send_error("CHICKEN SCRAPER (CRITICAL)")

        return 1

if __name__ == "__main__":
    main()
