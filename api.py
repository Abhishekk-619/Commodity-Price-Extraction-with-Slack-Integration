from typing import Optional
from enum import Enum
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import logging
from bson import ObjectId
from egg_price_schema import EggPriceDatabase

# Configure logging
logger = logging.getLogger(__name__)

def convert_objectid(doc):
    """Convert MongoDB ObjectId to string for JSON serialization"""
    if isinstance(doc, dict):
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                doc[key] = str(value)
            elif isinstance(value, dict):
                convert_objectid(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        convert_objectid(item)
    return doc

class Commodity(str, Enum):
    EGG = "egg"
    COPRA = "copra"
    CHICKEN = "chicken"

app = FastAPI(
    title="Egg Price API",
    description="API for retrieving and managing egg price data",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
try:
    db = EggPriceDatabase()
    # Add chicken prices collection
    db.chicken_prices = db.client["egg_price_data"]["chicken_prices_pw"]
    # Verify collections exist (check if they are None, not their truth value)
    if db.egg_prices is None:
        raise Exception("Egg prices collection not initialized")
    if db.copra_prices is None:
        raise Exception("Copra prices collection not initialized")
    if db.chicken_prices is None:
        raise Exception("Chicken prices collection not initialized")
    print("Successfully connected to all collections")
except Exception as e:
    print(f"Database connection error: {e}")
    raise

# Pydantic models for request/response validation
class EggPriceRate(BaseModel):
    price: Optional[float]
    quantity: int

class EggPriceData(BaseModel):
    single_egg: EggPriceRate
    tray: EggPriceRate
    hundred_eggs: EggPriceRate
    box: EggPriceRate

class CopraPriceData(BaseModel):
    min_price: Optional[float]
    max_price: Optional[float]
    avg_price: Optional[float]
    price_date: datetime

class ChickenPriceData(BaseModel):
    boneless: Optional[float]
    chicken: Optional[float]
    chicken_liver: Optional[float]
    country: Optional[float]
    live: Optional[float]
    skinless: Optional[float]
    date_of_price: str
    date_of_scraping: datetime

class PriceResponse(BaseModel):
    city: str
    rates: Optional[EggPriceData] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    avg_price: Optional[float] = None
    timestamp: datetime
    date: Optional[datetime] = None
    price_date: Optional[datetime] = None
    query_text: Optional[str] = None
    chicken_rates: Optional[ChickenPriceData] = None

@app.get("/")
async def root():
    """
    Root endpoint returning API information
    """
    return {"message": "Welcome to Egg Price API", "version": "1.0.0"}

@app.get("/prices/latest")
async def get_latest_prices(
    city: Optional[str] = Query(None, description="City name to filter prices"),
    commodity: Commodity = Query(Commodity.EGG, description="Commodity type (egg, copra, or chicken)")
):
    """
    Get latest prices for selected commodity for all cities or a specific city
    """
    try:
        if commodity == Commodity.EGG:
            collection = db.egg_prices
            if city:
                query = {'city': city.lower(), 'commodity': 'egg'}
                prices = list(collection.find(query).sort('date', -1).limit(1))
                if prices:
                    for price in prices:
                        convert_objectid(price)
                        if 'rates' in price:
                            price.update(price['rates'])
                            del price['rates']
            else:
                pipeline = [
                    {'$match': {'commodity': 'egg'}},
                    {'$sort': {'date': -1}},
                    {'$group': {
                        '_id': '$city',
                        'latest_price': {'$first': '$$ROOT'}
                    }},
                    {'$project': {
                        'latest_price': {
                            '$mergeObjects': [
                                '$latest_price',
                                {'$ifNull': ['$latest_price.rates', {}]}
                            ]
                        }
                    }}
                ]
                prices = list(collection.aggregate(pipeline))
                # Convert ObjectId to string for JSON serialization
                for price in prices:
                    convert_objectid(price)

        elif commodity == Commodity.COPRA:
            collection = db.copra_prices
            if city:
                query = {'city': city.lower()}
                prices = list(collection.find(query).sort('price_date', -1).limit(1))
                for price in prices:
                    convert_objectid(price)
            else:
                pipeline = [
                    {'$sort': {'price_date': -1}},
                    {'$group': {
                        '_id': '$city',
                        'latest_price': {'$first': '$$ROOT'}
                    }}
                ]
                prices = list(collection.aggregate(pipeline))
                for price in prices:
                    convert_objectid(price)

        else:  # CHICKEN
            collection = db.chicken_prices
            if city:
                if city.lower() in ['bangalore', 'bengaluru']:
                    query = {'city': {'$in': ['Bangalore', 'Bengaluru']}}
                else:
                    query = {'city': city.title()}
                prices = list(collection.find(query).sort('date_of_scraping', -1).limit(1))
                for price in prices:
                    convert_objectid(price)
            else:
                pipeline = [
                    {'$sort': {'date_of_scraping': -1}},
                    {'$group': {
                        '_id': '$city',
                        'latest_price': {'$first': '$$ROOT'}
                    }}
                ]
                prices = list(collection.aggregate(pipeline))
                for price in prices:
                    convert_objectid(price)

        if not prices:
            raise HTTPException(status_code=404, detail=f"No {commodity.value} price data found")

        # Format response for chicken
        if commodity == Commodity.CHICKEN:
            formatted_prices = []
            for price_doc in prices:
                if 'latest_price' in price_doc:
                    doc = price_doc['latest_price']
                else:
                    doc = price_doc

                chicken_data = {
                    "boneless": doc.get('boneless'),
                    "chicken": doc.get('chicken'),
                    "chicken_liver": doc.get('chicken_liver'),
                    "country": doc.get('country'),
                    "live": doc.get('live'),
                    "skinless": doc.get('skinless'),
                    "date_of_price": doc.get('date_of_price'),
                    "date_of_scraping": doc.get('date_of_scraping')
                }
                formatted_prices.append({"chicken_rates": chicken_data})
            return formatted_prices

        # For EGG and COPRA, return original format
        return prices
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from datetime import date as date_type

@app.get("/prices/historical")
async def get_historical_prices(
    city: str = Query(..., description="City name to get prices for"),
    date: date_type = Query(..., description="Date to get prices for (YYYY-MM-DD format)"),
    commodity: Commodity = Query(Commodity.EGG, description="Commodity type (egg, copra, or chicken)")
):
    """
    Get prices for selected commodity for a specific city and date
    """
    try:
        if commodity == Commodity.EGG:
            collection = db.egg_prices
            start_datetime = datetime.combine(date, datetime.min.time())
            end_datetime = datetime.combine(date, datetime.max.time())
            price_data = collection.find_one({
                'city': city.lower(),
                'commodity': 'egg',
                'date': {
                    '$gte': start_datetime,
                    '$lte': end_datetime
                }
            })
            if not price_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"No egg price data found for {city} on {date}"
                )
            convert_objectid(price_data)
            if 'rates' in price_data:
                price_data.update(price_data['rates'])
                del price_data['rates']
            return price_data

        elif commodity == Commodity.COPRA:
            collection = db.copra_prices
            start_datetime = datetime.combine(date, datetime.min.time())
            end_datetime = datetime.combine(date, datetime.max.time())
            price_data = collection.find_one({
                'city': city.lower(),
                'price_date': {
                    '$gte': start_datetime,
                    '$lte': end_datetime
                }
            })
            if not price_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"No copra price data found for {city} on {date}"
                )
            convert_objectid(price_data)
            return price_data

        else:  # CHICKEN
            collection = db.chicken_prices
            date_str = date.strftime('%Y-%m-%d')
            if city.lower() in ['bangalore', 'bengaluru']:
                price_data = collection.find_one({
                    'city': {'$in': ['Bangalore', 'Bengaluru']},
                    'date_of_price': date_str
                })
            else:
                price_data = collection.find_one({
                    'city': city.title(),
                    'date_of_price': date_str
                })
            if not price_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"No chicken price data found for {city} on {date_str}"
                )

            convert_objectid(price_data)
            formatted_price = {
                'city': price_data['city'],
                'timestamp': price_data['date_of_scraping'],
                'chicken_rates': {
                    'boneless': price_data.get('boneless'),
                    'chicken': price_data.get('chicken'),
                    'chicken_liver': price_data.get('chicken_liver'),
                    'country': price_data.get('country'),
                    'live': price_data.get('live'),
                    'skinless': price_data.get('skinless'),
                    'date_of_price': price_data.get('date_of_price'),
                    'date_of_scraping': price_data['date_of_scraping']
                }
            }
            return formatted_price
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cities")
async def get_available_cities(commodity: Commodity = Query(Commodity.EGG, description="Commodity type (egg or copra)")):
    """
    Get a list of available cities based on the commodity type
    """
    try:
        if commodity == Commodity.EGG:
            cities = ['bengaluru', 'mumbai', 'chennai', 'kolkata', 'delhi', 'hyderabad']
        elif commodity == Commodity.COPRA:
            cities = ['bangalore', 'chennai', 'mumbai', 'delhi', 'hyderabad', 'kolkata', 'pune', 'thiruvananthapuram', 
                     'surat', 'kochi', 'coimbatore', 'mangaluru', 'visakhapatnam', 'madurai', 'kozhikode', 'ahmedabad', 
                     'gandhidham', 'bhadohi', 'indore', 'pollachi', 'tiptur', 'secunderabad', 'mandya', 'namakkal', 
                     'erode', 'mysore', 'thane', 'cuttack', 'karikkad', 'doiwala', 'jaipur', 'agra', 'gurugram', 
                     'loni', 'kanpur', 'tumakuru', 'hosur', 'vasai-virar', 'panvel', 'nashik', 'karjat', 'vellakovil', 
                     'udumalpet', 'hassan', 'salem', 'hubli', 'gobichettipalayam', 'nagpur', 'raipur', 'patna', 
                     'amritsar', 'noida', 'rajkot', 'varanasi', 'lucknow', 'bhopal', 'theni-allinagaram', 
                     'navi-mumbai', 'new-delhi']
        else:
            cities = ['mumbai', 'chennai', 'bangalore', 'hyderabad', 'delhi', 'kolkata', 'ahmedabad', 'madurai',
                     'visakhapatnam', 'lucknow', 'vijayawada', 'surat', 'patna', 'kochi', 'jaipur', 'mysore',
                     'trivandrum', 'vadodara', 'nagpur', 'coimbatore', 'pune', 'bhubaneswar', 'nashik']
        return {"cities": cities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/prices/range")
async def get_prices_by_date_range(
    city: str = Query(..., description="City name to get prices for"),
    start_date: date_type = Query(..., description="Start date (YYYY-MM-DD format)"),
    end_date: date_type = Query(..., description="End date (YYYY-MM-DD format)"),
    commodity: Commodity = Query(Commodity.EGG, description="Commodity type (egg, copra, or chicken)")
):
    """
    Get prices for selected commodity for a specific city within a date range
    """
    try:
        if commodity == Commodity.EGG:
            collection = db.egg_prices
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            prices = list(collection.find({
                'city': city.lower(),
                'commodity': 'egg',
                'date': {
                    '$gte': start_datetime,
                    '$lte': end_datetime
                }
            }).sort('date', 1))
            
            if not prices:
                raise HTTPException(
                    status_code=404,
                    detail=f"No egg price data found for {city} between {start_date} and {end_date}"
                )
            
            for price in prices:
                convert_objectid(price)
                if 'rates' in price:
                    price.update(price['rates'])
                    del price['rates']
            return prices

        elif commodity == Commodity.COPRA:
            collection = db.copra_prices
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            prices = list(collection.find({
                'city': city.lower(),
                'price_date': {
                    '$gte': start_datetime,
                    '$lte': end_datetime
                }
            }).sort('price_date', 1))
            
            if not prices:
                raise HTTPException(
                    status_code=404,
                    detail=f"No copra price data found for {city} between {start_date} and {end_date}"
                )
            for price in prices:
                convert_objectid(price)
            return prices

        else:  # CHICKEN
            collection = db.chicken_prices
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            if city.lower() in ['bangalore', 'bengaluru']:
                query = {'city': {'$in': ['Bangalore', 'Bengaluru']}}
            else:
                query = {'city': city.title()}
            
            query['date_of_price'] = {
                '$gte': start_str,
                '$lte': end_str
            }
            
            prices = list(collection.find(query).sort('date_of_scraping', 1))
            
            if not prices:
                raise HTTPException(
                    status_code=404,
                    detail=f"No chicken price data found for {city} between {start_str} and {end_str}"
                )
            
            formatted_prices = []
            for price in prices:
                convert_objectid(price)
                formatted_price = {
                    'city': price['city'],
                    'timestamp': price['date_of_scraping'],
                    'chicken_rates': {
                        'boneless': price.get('boneless'),
                        'chicken': price.get('chicken'),
                        'chicken_liver': price.get('chicken_liver'),
                        'country': price.get('country'),
                        'live': price.get('live'),
                        'skinless': price.get('skinless'),
                        'date_of_price': price.get('date_of_price'),
                        'date_of_scraping': price['date_of_scraping']
                    }
                }
                formatted_prices.append(formatted_price)
            return formatted_prices
    except Exception as e:
        logger.error(f"Error in get_prices_by_date_range: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching price range data")

@app.on_event("shutdown")
def shutdown_event():
    """
    Close database connection on shutdown
    """
    db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)