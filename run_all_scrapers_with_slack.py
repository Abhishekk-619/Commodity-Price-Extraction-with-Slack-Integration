"""
Master Script to Run All Commodity Scrapers with Slack Notifications
===================================================================

This script runs all commodity price scrapers (egg, copra, chicken) with 
integrated Slack notifications. Each scraper will send success/error messages
to your configured Slack channel.

Usage:
    python run_all_scrapers_with_slack.py

Before running:
    1. Insert your Slack webhook URL in slack_notifier.py
    2. Ensure MongoDB is running
    3. Install all required dependencies
"""

import asyncio
import sys
import traceback
from datetime import datetime
from slack_notifier import SlackNotifier

# Import the enhanced scrapers
from egg_scraper_with_slack import EggScraperWithSlack
from copra_scraper_with_slack import CopraPriceScraperWithSlack
from chicken_scraper_with_slack import ChickenPriceScraperWithSlack


class MasterScraperRunner:
    """Master runner for all commodity scrapers with Slack notifications"""
    
    def __init__(self):
        """Initialize the master runner"""
        self.slack = SlackNotifier()
        self.results = {
            'egg': False,
            'copra': False,
            'chicken': False
        }
        
    def print_header(self):
        """Print a nice header for the scraping session"""
        print("=" * 80)
        print("🚀 COMMODITY PRICE SCRAPER SUITE WITH SLACK NOTIFICATIONS 🚀")
        print("=" * 80)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("📊 Scrapers: Egg, Copra, Chicken")
        print("📱 Slack notifications: Enabled")
        print("=" * 80)
        
    def run_egg_scraper(self):
        """Run the egg price scraper"""
        print("\n" + "="*50)
        print("🥚 STARTING EGG PRICE SCRAPER")
        print("="*50)
        
        scraper = None
        try:
            scraper = EggScraperWithSlack()
            success = scraper.run_scraping()
            self.results['egg'] = success
            
            if success:
                print("✅ Egg scraper completed successfully!")
            else:
                print("❌ Egg scraper failed!")
                
        except Exception as e:
            print(f"❌ Critical error in egg scraper: {str(e)}")
            traceback.print_exc()
            self.results['egg'] = False
            
            # Send error notification
            try:
                if scraper and hasattr(scraper, 'slack'):
                    scraper.slack.send_error("EGG SCRAPER")
                else:
                    self.slack.send_error("EGG SCRAPER")
            except:
                pass
                
        finally:
            if scraper:
                try:
                    scraper.close()
                except:
                    pass
    
    def run_copra_scraper(self):
        """Run the copra price scraper"""
        print("\n" + "="*50)
        print("🥥 STARTING COPRA PRICE SCRAPER")
        print("="*50)
        
        scraper = None
        try:
            scraper = CopraPriceScraperWithSlack()
            success = scraper.run_scraping()
            self.results['copra'] = success
            
            if success:
                print("✅ Copra scraper completed successfully!")
            else:
                print("❌ Copra scraper failed!")
                
        except Exception as e:
            print(f"❌ Critical error in copra scraper: {str(e)}")
            traceback.print_exc()
            self.results['copra'] = False
            
            # Send error notification
            try:
                if scraper and hasattr(scraper, 'slack'):
                    scraper.slack.send_error("COPRA SCRAPER")
                else:
                    self.slack.send_error("COPRA SCRAPER")
            except:
                pass
                
        finally:
            if scraper:
                try:
                    scraper.close()
                except:
                    pass
    
    async def run_chicken_scraper(self):
        """Run the chicken price scraper"""
        print("\n" + "="*50)
        print("🐔 STARTING CHICKEN PRICE SCRAPER")
        print("="*50)
        
        scraper = None
        try:
            scraper = ChickenPriceScraperWithSlack()
            success = await scraper.run_scraping()
            self.results['chicken'] = success
            
            if success:
                print("✅ Chicken scraper completed successfully!")
            else:
                print("❌ Chicken scraper failed!")
                
        except Exception as e:
            print(f"❌ Critical error in chicken scraper: {str(e)}")
            traceback.print_exc()
            self.results['chicken'] = False
            
            # Send error notification
            try:
                if scraper and hasattr(scraper, 'slack'):
                    scraper.slack.send_error("CHICKEN SCRAPER")
                else:
                    self.slack.send_error("CHICKEN SCRAPER")
            except:
                pass
    
    def print_summary(self):
        """Print final summary of all scraping results"""
        print("\n" + "="*80)
        print("📊 SCRAPING SESSION SUMMARY")
        print("="*80)
        
        total_scrapers = len(self.results)
        successful_scrapers = sum(1 for success in self.results.values() if success)
        
        print(f"📅 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📈 Success rate: {successful_scrapers}/{total_scrapers} ({(successful_scrapers/total_scrapers)*100:.1f}%)")
        print()
        
        # Individual results
        for scraper_name, success in self.results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"  {scraper_name.upper()} SCRAPER: {status}")
        
        print("="*80)
        
        # Overall status
        if successful_scrapers == total_scrapers:
            print("🎉 ALL SCRAPERS COMPLETED SUCCESSFULLY!")
        elif successful_scrapers > 0:
            print(f"⚠️  {successful_scrapers} out of {total_scrapers} scrapers completed successfully")
        else:
            print("❌ ALL SCRAPERS FAILED!")
        
        print("="*80)
    
    async def run_all_scrapers(self):
        """Run all scrapers in sequence"""
        self.print_header()
        
        # Check if Slack is configured
        if not self.slack.is_configured:
            print("⚠️  WARNING: Slack webhook URL not configured!")
            print("   Notifications will be printed to console only.")
            print("   To enable Slack notifications, update the webhook URL in slack_notifier.py")
            print()
        
        try:
            # Run egg scraper
            self.run_egg_scraper()
            
            # Run copra scraper
            self.run_copra_scraper()
            
            # Run chicken scraper (async)
            await self.run_chicken_scraper()
            
        except KeyboardInterrupt:
            print("\n⚠️ Scraping interrupted by user!")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Unexpected error in master runner: {str(e)}")
            traceback.print_exc()
        
        finally:
            # Always print summary
            self.print_summary()


async def main():
    """Main function to run all scrapers"""
    try:
        runner = MasterScraperRunner()
        await runner.run_all_scrapers()
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
