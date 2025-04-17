# MongoDB Integration for Egg Price Agent

This extension adds MongoDB database integration to the Egg Price Agent, allowing it to store user queries and agent responses for future analysis and reference.

## Schema Design

The MongoDB schema is designed to store the following information:

- **query_text**: The original question asked by the user
- **response_text**: The response provided by the agent
- **query_timestamp**: When the query was made
- **city**: The city mentioned in the query (if any)
- **price_data**: Structured price data extracted from the response

## Setup Instructions

### Prerequisites

1. MongoDB installed locally or a MongoDB Atlas account
2. Python 3.6 or higher
3. Required Python packages (install using `pip install -r requirements.txt`):
   - requests
   - beautifulsoup4
   - pymongo

### Configuration

By default, the integration connects to a local MongoDB instance at `mongodb://localhost:27017/` and uses a database named `egg_price_agent`. You can customize these settings when initializing the agent:

```python
# Connect to a custom MongoDB instance
agent = EggPriceAgentWithDB(
    connection_string="mongodb://username:password@your-mongodb-host:27017/",
    db_name="your_database_name"
)
```

## Usage

To use the Egg Price Agent with database integration:

```python
from egg_price_agent_with_db import EggPriceAgentWithDB

# Initialize the agent with database integration
agent = EggPriceAgentWithDB()

# Process a user query
query = "Show me the price of eggs today"
response = agent.process_query(query)
print(response)

# Always close the connection when done
agent.close()
```

## Data Access

You can access the stored data using the `EggPriceDatabase` class directly:

```python
from db_schema import EggPriceDatabase

# Initialize the database connection
db = EggPriceDatabase()

# Get recent queries
recent_queries = db.get_recent_queries(limit=5)
for query in recent_queries:
    print(f"Query: {query['query_text']}")
    print(f"Response: {query['response_text']}")
    print(f"Timestamp: {query['query_timestamp']}")
    print("---")

# Get queries for a specific city
delhi_queries = db.get_queries_by_city("delhi", limit=3)

# Close the connection when done
db.close_connection()
```

## Files

- `db_schema.py`: Defines the MongoDB schema and database connection utilities
- `db_integration.py`: Provides integration between the Egg Price Agent and MongoDB
- `egg_price_agent_with_db.py`: Wrapper class that extends the original agent with database functionality

## Future Enhancements

- Add query analytics and reporting
- Implement caching to reduce redundant web scraping
- Add user identification for personalized responses
- Create a web interface for browsing stored queries and responses