from egg_price_agent import EggPriceAgent
from db_integration import DatabaseIntegration

"""
Egg Price Agent with Database Integration

This module extends the original EggPriceAgent with database functionality
to store user queries and agent responses in MongoDB.
"""


class EggPriceAgentWithDB:
    def __init__(self, connection_string="mongodb://localhost:27017/", db_name="egg_price_agent"):
        """
        Initialize the agent with database integration
        
        Args:
            connection_string (str): MongoDB connection string
            db_name (str): Name of the database
        """
        self.agent = EggPriceAgent()
        self.db_integration = DatabaseIntegration(connection_string, db_name)
    
    def process_query(self, query):
        """
        Process a user query and store the interaction in the database
        
        Args:
            query (str): The user's query about egg prices
            
        Returns:
            str: The agent's response
        """
        # Get response from the original agent
        response = self.agent.process_query(query)
        
        # Store the interaction in the database
        self.db_integration.store_interaction(query, response, self.agent)
        
        return response
    
    def close(self):
        """
        Close the database connection
        """
        self.db_integration.close()


# Example usage
if __name__ == "__main__":
    # Create the agent with database integration
    agent = EggPriceAgentWithDB()
    
    # Process a sample query
    query = "Show me the price of eggs today"
    response = agent.process_query(query)
    print(f"Query: {query}")
    print(f"Response:\n{response}")
    
    # Close the database connection when done
    agent.close()