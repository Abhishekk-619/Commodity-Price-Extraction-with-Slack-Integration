# Egg Price Agent

A simple Python-based AI agent that fetches egg prices from eggpricetoday.com and provides them to users through a command-line interface.

## Features

- Fetches current egg prices from eggpricetoday.com
- Processes natural language queries about egg prices
- Returns formatted price information for different types of eggs
- Provides two implementation options: BeautifulSoup and FireCrawl

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```
pip install -r requirements.txt
```

## Usage

This project provides two different implementations:

### BeautifulSoup Implementation

Run the agent using Python:

```
python egg_price_agent.py
```

### FireCrawl Implementation

Run the alternative implementation that uses FireCrawl:

```
python egg_price_agent_firecrawl.py
```

### Interacting with the Agent

Once the agent is running, you can ask questions about egg prices such as:
- "What is the price of eggs today?"
- "How much do eggs cost?"
- "Tell me the current egg prices"

Type 'exit' to quit the application.

## How It Works

### BeautifulSoup Implementation

The `egg_price_agent.py` implementation uses BeautifulSoup for web scraping to extract egg price information from eggpricetoday.com. It processes user queries to determine if they're asking about egg prices, then fetches and formats the current prices.

### FireCrawl Implementation

The `egg_price_agent_firecrawl.py` implementation uses FireCrawl, which is a more powerful web crawling library. FireCrawl provides additional capabilities for handling dynamic content and complex web pages, which may be beneficial if the website structure is complex or changes frequently.

## Note

This agent is for educational purposes. The website structure of eggpricetoday.com may change over time, which could affect the agent's ability to extract prices correctly. You may need to update the selectors in the `fetch_egg_prices` method if this happens.