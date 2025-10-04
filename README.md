This project is a comprehensive system designed to extract, store, and present commodity price data, specifically for eggs, chicken, and copra. It leverages various web scraping techniques, integrates with a database for data persistence, provides an API for data access, and includes notification features.

Here's a detailed breakdown of its components:

1. 
   Web Scrapers :
   
   - Egg Price Scrapers :
     - `egg_price_agent_firecrawl.py` : This script is responsible for scraping real-time egg prices from eggpricetoday.com . It uses requests to fetch the webpage content and BeautifulSoup to parse the HTML and extract price data for various cities and quantities (1pc, 30pcs, 100pcs, 210pcs). It also includes fallback mechanisms to hardcoded data if scraping fails.
     - `egg_price_agent_firecrawl_with_db.py` : This extends the egg_price_agent_firecrawl.py by integrating with a MongoDB database to store the scraped egg prices. It also incorporates historical data scraping.
     - `egg_price_historical_scraper.py` : This script likely focuses on gathering historical egg price data, complementing the real-time scraper.
   - Chicken Price Scrapers :
     - `chicken_price_scraper_playwright.py` : This scraper uses Playwright , a browser automation library, to extract chicken prices. Playwright is ideal for websites with dynamic content loaded via JavaScript, as it can interact with the page like a real user.
     - `linux_chicken_scraper_fixed.py` : This suggests a version of the chicken scraper specifically adapted or fixed for Linux environments.
   - Copra Scrapers :
     - `copra_scraper.py` : This script is dedicated to scraping copra prices. The specific technology used would need further inspection of the file, but it likely uses requests and BeautifulSoup similar to the egg scraper, or potentially Playwright if the source is dynamic.
2. 
   Database Integration :
   
   - `egg_price_schema.py` : This file defines the schema and interaction logic for storing egg price data, specifically utilizing pymongo for a MongoDB database.
   - `test_db.py` : A script for testing the database interactions.
3. 
   API :
   
   - `api.py` : This file implements a FastAPI application that serves the collected commodity price data. It provides endpoints to:
     - Get the latest prices for eggs, copra, and chicken, either for all cities or a specific city.
     - Retrieve historical prices for a given city and date.
     - Fetch prices within a specified date range for a particular city.
     - List available cities for each commodity.
     - It connects to the MongoDB database to retrieve the data.
4. 
   Slack Notifications :
   
   - `slack_notifier.py` : This module handles sending notifications to Slack channels. It likely takes a webhook URL and a message to post.
   - `chicken_scraper_with_slack.py` , `copra_scraper_with_slack.py` , `egg_scraper_with_slack.py` : These scripts integrate the respective scrapers with the slack_notifier to send automated notifications about scraping status, errors, or perhaps significant price changes.
   - `slack_setup_instructions.md` : Provides guidance on setting up Slack for notifications.
5. 
   Automation and Deployment :
   
   - `run_all_scrapers_with_slack.py` : A central script to execute all the scrapers, likely in an automated fashion, and integrate with Slack notifications.
   - `run_historical_scraper.py` : A script to specifically run the historical data scraper.
   - `start_scraper.sh` : A shell script for initiating the scraping process, likely for deployment or scheduled tasks.
   - `deployment_guide.md` : Provides instructions for deploying the entire system.
   - `process_framework.md` : Likely outlines the overall architecture and workflow of the commodity extraction process.
6. 
   Dependencies :
   
   - `requirements.txt` : Lists all the Python libraries required for the project, including requests , beautifulsoup4 , pymongo , fastapi , uvicorn , pydantic , python-dotenv , playwright , streamlit , plotly , and pandas .
