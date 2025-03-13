# Script to fetch reviews
#!/usr/bin/env python3
import sys
import os
import argparse
import logging
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import GoogleReviewScraper
from database import ReviewDatabase
from sentiment_analysis import SentimentAnalyzer
from config import validate_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/fetch_reviews.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def fetch_reviews(place_id, max_reviews=100):
    """
    Fetch reviews for a business
    
    Args:
        place_id (str): Google Places ID
        max_reviews (int): Maximum number of reviews to fetch
    
    Returns:
        int: Number of reviews fetched
    """
    try:
        logger.info(f"Fetching reviews for place ID: {place_id}")
        start_time = time.time()
        
        # Initialize components
        scraper = GoogleReviewScraper()
        db = ReviewDatabase()
        analyzer = SentimentAnalyzer()
        
        # Fetch basic business info
        business_info = scraper.get_business_info(place_id)
        if business_info:
            business_info['place_id'] = place_id
            db.insert_business_info(business_info)
        
        # Fetch reviews
        reviews = scraper.fetch_reviews(place_id, max_reviews)
        
        # Process reviews
        for review in reviews:
            # Analyze sentiment
            sentiment = analyzer.analyze_text(review.get('text', ''))
            review['sentiment'] = sentiment
            
            # Extract keywords
            keywords = analyzer.extract_keywords(review.get('text', ''))
            review['keywords'] = keywords
        
        # Store reviews
        count = db.insert_reviews(reviews, place_id)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Fetched and processed {count} reviews in {elapsed_time:.2f} seconds")
        
        return count
    
    except Exception as e:
        logger.error(f"Error fetching reviews: {str(e)}")
        return 0

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Fetch Google reviews for a business')
    parser.add_argument('place_id', help='Google Places ID for the business')
    parser.add_argument('--max', type=int, default=100, help='Maximum number of reviews to fetch')
    args = parser.parse_args()
    
    # Validate configuration
    if not validate_config():
        logger.error("Invalid configuration. Please check your environment variables.")
        sys.exit(1)
    
    # Fetch reviews
    count = fetch_reviews(args.place_id, args.max)
    
    print(f"Fetched {count} reviews for place ID: {args.place_id}")

if __name__ == '__main__':
    main()