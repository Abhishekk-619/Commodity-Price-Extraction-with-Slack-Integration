# Egg Price Agent Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [MongoDB Setup](#mongodb-setup)
4. [Project Installation](#project-installation)
5. [Configuration](#configuration)
6. [Running the Application](#running-the-application)
7. [Deployment Options](#deployment-options)
8. [Security Considerations](#security-considerations)
9. [Maintenance](#maintenance)

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)
- MongoDB 4.4 or higher
- Git (optional, for version control)

## Environment Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   - Windows:
     ```bash
     .\venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

3. Install required dependencies:
   ```bash
   pip install pymongo requests beautifulsoup4
   ```

## MongoDB Setup

1. Install MongoDB:
   - Download MongoDB Community Server from the [official website](https://www.mongodb.com/try/download/community)
   - Follow the installation instructions for your operating system

2. Start MongoDB service:
   - Windows: MongoDB should run as a service automatically
   - Linux/Mac: 
     ```bash
     sudo systemctl start mongod
     ```

3. Verify MongoDB connection:
   - The application will automatically test the connection when started
   - Default connection string: `mongodb://localhost:27017/`

## Project Installation

1. Clone or download the project files:
   - Place all Python files in your desired directory
   - Ensure you have all required files:
     - `egg_price_agent_firecrawl_with_db.py`
     - `egg_price_schema.py`
     - `egg_price_historical_scraper.py`
     - `egg_price_agent_firecrawl.py`

2. Configure MongoDB connection:
   - Open `egg_price_agent_firecrawl_with_db.py`
   - Modify the connection string if needed:
     ```python
     connection_string="mongodb://localhost:27017/"
     db_name="egg_price_data"
     ```

## Configuration

1. City Configuration:
   - Supported cities are defined in `_store_initial_prices()`
   - Current supported cities:
     - Bengaluru
     - Chennai
     - Mumbai
     - Hyderabad
     - Kolkata
     - Delhi

2. Database Configuration:
   - Default database name: `egg_price_data`
   - Default collection: `egg_prices`
   - Customize by modifying the `db_name` parameter

## Running the Application

1. Start the application:
   ```bash
   python egg_price_agent_firecrawl_with_db.py
   ```

2. Verify successful startup:
   - Check for MongoDB connection message
   - Confirm initial price data is loaded
   - Test with a sample query

## Deployment Options

### Local Deployment
- Suitable for development and testing
- Run directly using Python interpreter
- Keep the virtual environment activated

### Cloud Deployment

1. MongoDB Atlas (Cloud Database):
   - Create account on [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
   - Set up a new cluster
   - Update connection string with Atlas URI
   - Enable network access for your application

2. Cloud Platform Options:
   - Heroku:
     - Create Procfile: `web: python egg_price_agent_firecrawl_with_db.py`
     - Set environment variables for MongoDB connection
     - Deploy using Heroku CLI or GitHub integration
   
   - AWS EC2:
     - Launch EC2 instance
     - Install Python and dependencies
     - Use systemd service for automatic startup
     - Configure security groups for MongoDB access

## Security Considerations

1. MongoDB Security:
   - Enable authentication
   - Use strong passwords
   - Restrict network access
   - Regular security updates

2. Application Security:
   - Store sensitive data in environment variables
   - Validate user input
   - Implement rate limiting
   - Regular dependency updates

3. Best Practices:
   - Use HTTPS for cloud deployments
   - Implement logging
   - Regular backups
   - Monitor system resources

## Maintenance

1. Regular Tasks:
   - Monitor logs for errors
   - Check MongoDB performance
   - Update dependencies
   - Backup database regularly

2. Troubleshooting:
   - Check MongoDB connection
   - Verify network connectivity
   - Review error logs
   - Test data scraping functionality

3. Updates:
   - Keep Python packages updated
   - Monitor for security patches
   - Test updates in development environment
   - Maintain documentation

## Support

For issues and support:
1. Check error messages and logs
2. Review MongoDB documentation
3. Verify network connectivity
4. Check system resources

---

This deployment guide provides comprehensive instructions for setting up and maintaining the Egg Price Agent. Follow each section carefully and ensure all prerequisites are met before deployment.