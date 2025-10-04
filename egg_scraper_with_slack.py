"""
Egg Price Scraper with Slack Notifications
==========================================

Enhanced version of the egg price scraper with integrated Slack notifications.
Sends success/error messages to Slack channel automatically.
"""

from egg_price_agent_firecrawl_with_db import EggPriceAgentFireCrawlWithDB
from slack_notifier import SlackNotifier
import traceback


class EggScraperWithSlack:
    """Egg price scraper with Slack notification integration"""
    
    def __init__(self, connection_string="mongodb://localhost:27017/", db_name="egg_price_data"):
        """Initialize the scraper with Slack notifications"""
        self.scraper = EggPriceAgentFireCrawlWithDB(connection_string, db_name)
        self.slack = SlackNotifier()
        self.scraper_name = "EGG SCRAPER"
    
    def run_scraping(self):
        """
        Run the egg price scraping with Slack notifications
        
        Returns:
            bool: True if scraping succeeded, False if failed
        """
        try:
            print("Starting egg price scraping...")
            
            # The EggPriceAgentFireCrawlWithDB automatically scrapes and stores data
            # during initialization via _store_initial_prices() and _store_historical_prices()
            # So we just need to check if it completed successfully
            
            # Verify that the scraper is working by checking if we can get latest prices
            latest_prices = self.scraper.db.get_latest_prices()
            
            if latest_prices and len(latest_prices) > 0:
                print(f"✅ Egg scraping completed successfully! Found data for {len(latest_prices)} cities.")
                self.slack.send_success(self.scraper_name)
                return True
            else:
                print("❌ Egg scraping failed - no data found")
                self.slack.send_error(self.scraper_name)
                return False
                
        except Exception as e:
            print(f"❌ Egg scraping failed with error: {str(e)}")
            print("Full error traceback:")
            traceback.print_exc()
            self.slack.send_error(self.scraper_name)
            return False
    
    def close(self):
        """Close database connections"""
        try:
            self.scraper.close()
        except:
            pass


def main():
    """Main function to run egg scraper with Slack notifications"""
    scraper = None
    try:
        print("=" * 60)
        print("🥚 Egg Price Scraper with Slack Notifications 🥚")
        print("=" * 60)
        
        # Initialize and run scraper
        scraper = EggScraperWithSlack()
        success = scraper.run_scraping()
        
        if success:
            print("\n✅ Egg price scraping completed successfully!")
        else:
            print("\n❌ Egg price scraping failed!")
            
    except Exception as e:
        print(f"\n❌ Critical error in egg scraper: {str(e)}")
        traceback.print_exc()
        
        # Send error notification if scraper object exists
        if scraper and hasattr(scraper, 'slack'):
            scraper.slack.send_error("EGG SCRAPER")
        else:
            # Fallback notification
            slack = SlackNotifier()
            slack.send_error("EGG SCRAPER")
    
    finally:
        # Clean up
        if scraper:
            scraper.close()


if __name__ == "__main__":
    main()
