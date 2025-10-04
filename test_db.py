#!/usr/bin/env python3

from egg_price_schema import EggPriceDatabase
from datetime import datetime

def test_database():
    """Test database connection and basic operations"""
    try:
        print("Testing database connection...")
        db = EggPriceDatabase()
        
        print("Testing egg prices collection...")
        # Test if we can query the egg prices collection
        egg_count = db.egg_prices.count_documents({})
        print(f"Total egg price documents: {egg_count}")
        
        # Test with commodity filter
        egg_count_with_commodity = db.egg_prices.count_documents({'commodity': 'egg'})
        print(f"Egg price documents with commodity='egg': {egg_count_with_commodity}")
        
        print("Testing copra prices collection...")
        # Test copra prices collection
        copra_count = db.copra_prices.count_documents({})
        print(f"Total copra price documents: {copra_count}")
        
        print("Testing aggregation pipeline...")
        # Test the aggregation pipeline that's causing issues
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
        
        result = list(db.egg_prices.aggregate(pipeline))
        print(f"Aggregation result count: {len(result)}")
        if result:
            print("Sample result:", result[0])
        
        print("Database test completed successfully!")
        
    except Exception as e:
        print(f"Database test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    test_database()
