from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel
from egg_price_schema import EggPriceDatabase

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
db = EggPriceDatabase()

# Pydantic models for request/response validation
class EggPriceRate(BaseModel):
    price: Optional[float]
    quantity: int

class EggPriceData(BaseModel):
    single_egg: EggPriceRate
    tray: EggPriceRate
    hundred_eggs: EggPriceRate
    box: EggPriceRate

class EggPriceResponse(BaseModel):
    city: str
    rates: EggPriceData
    timestamp: datetime
    date: datetime
    query_text: str

@app.get("/")
async def root():
    """
    Root endpoint returning API information
    """
    return {"message": "Welcome to Egg Price API", "version": "1.0.0"}

@app.get("/prices/latest", response_model=List[EggPriceResponse])
async def get_latest_prices(city: Optional[str] = Query(None, description="City name to filter prices")):
    """
    Get latest egg prices for all cities or a specific city
    """
    try:
        prices = db.get_latest_prices(city)
        if not prices:
            raise HTTPException(status_code=404, detail="No price data found")
        return prices
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from datetime import date as date_type

@app.get("/prices/historical")
async def get_historical_prices(
    city: str = Query(..., description="City name to get prices for"),
    date: date_type = Query(..., description="Date to get prices for (YYYY-MM-DD format)")
):
    """
    Get egg prices for a specific city and date
    """
    try:
        prices = db.get_prices_by_date(city, date)
        if not prices:
            raise HTTPException(status_code=404, detail="No price data found for the specified city and date")
        return prices
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cities")
async def get_available_cities():
    """
    Get a list of all cities that have egg price data
    """
    try:
        cities = db.get_available_cities()
        if not cities:
            raise HTTPException(status_code=404, detail="No cities found")
        return {"cities": cities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
def shutdown_event():
    """
    Close database connection on shutdown
    """
    db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)