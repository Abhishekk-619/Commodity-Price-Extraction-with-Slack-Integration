import schedule
import time
from egg_price_agent_firecrawl_with_db import EggPriceAgentFireCrawlWithDB
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('egg_price_cron.log'),
        logging.StreamHandler()
    ]
)

class EggPriceCronJob:
    def __init__(self, connection_string="mongodb://localhost:27017/", db_name="egg_price_data"):
        self.connection_string = connection_string
        self.db_name = db_name
        self.agent = None

    def update_prices(self):
        """Update egg prices in the database"""
        try:
            logging.info("Starting egg price update job")
            
            # Create a new agent instance for each update to ensure fresh connections
            self.agent = EggPriceAgentFireCrawlWithDB(
                connection_string=self.connection_string,
                db_name=self.db_name
            )
            logging.info("Successfully updated egg prices")
            
        except Exception as e:
            logging.error(f"Error updating egg prices: {e}")
        finally:
            if self.agent:
                self.agent.close()
                self.agent = None

def main():
    # Initialize the cron job
    cron_job = EggPriceCronJob()
    
    # Schedule price updates
    # Run every day at 9:00 AM and 5:00 PM (market opening and closing times)
    schedule.every().day.at("09:00").do(cron_job.update_prices)
    schedule.every().day.at("17:00").do(cron_job.update_prices)
    
    logging.info("Egg Price Cron Job started. Waiting for scheduled runs...")
    
    # Keep the script running
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logging.info("Shutting down cron job...")
            break
        except Exception as e:
            logging.error(f"Unexpected error in main loop: {e}")
            # Wait for 5 minutes before retrying in case of errors
            time.sleep(300)

if __name__ == "__main__":
    main()