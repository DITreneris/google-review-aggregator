# Flask API (Handles backend requests)
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from database import ReviewDatabase
from scraper import GoogleReviewScraper
from sentiment_analysis import SentimentAnalyzer

# Configure logging
logging.basicConfig(
    filename='logs/app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Initialize components
db = ReviewDatabase()
scraper = GoogleReviewScraper()
sentiment_analyzer = SentimentAnalyzer()

@app.route('/api/fetch-reviews', methods=['POST'])
def fetch_reviews():
    """Endpoint to trigger review fetching for a business"""
    try:
        data = request.get_json()
        place_id = data.get('place_id')
        
        if not place_id:
            return jsonify({'error': 'Place ID is required'}), 400
        
        # Fetch reviews using the scraper
        reviews = scraper.fetch_reviews(place_id)
        
        # Analyze sentiment for each review
        for review in reviews:
            review['sentiment'] = sentiment_analyzer.analyze_text(review['text'])
        
        # Store reviews in database
        db.insert_reviews(reviews, place_id)
        
        return jsonify({
            'success': True,
            'reviews_count': len(reviews)
        })
    
    except Exception as e:
        logger.error(f"Error fetching reviews: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    """Endpoint to retrieve reviews for a business"""
    try:
        place_id = request.args.get('place_id')
        
        if not place_id:
            return jsonify({'error': 'Place ID is required'}), 400
        
        # Optional filters
        rating = request.args.get('rating')
        sentiment = request.args.get('sentiment')
        limit = request.args.get('limit', 100)
        offset = request.args.get('offset', 0)
        
        # Get reviews from database
        reviews = db.get_reviews(
            place_id, 
            rating=rating, 
            sentiment=sentiment,
            limit=limit,
            offset=offset
        )
        
        return jsonify({
            'success': True,
            'reviews': reviews
        })
    
    except Exception as e:
        logger.error(f"Error retrieving reviews: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Endpoint to get review statistics for a business"""
    try:
        place_id = request.args.get('place_id')
        
        if not place_id:
            return jsonify({'error': 'Place ID is required'}), 400
        
        # Get review statistics
        stats = db.get_review_stats(place_id)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    
    except Exception as e:
        logger.error(f"Error retrieving statistics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/business-info', methods=['GET'])
def get_business_info():
    """Endpoint to get business information"""
    try:
        place_id = request.args.get('place_id')
        
        if not place_id:
            return jsonify({'error': 'Place ID is required'}), 400
        
        # Get business info from the scraper
        business_info = scraper.get_business_info(place_id)
        
        return jsonify({
            'success': True,
            'business_info': business_info
        })
    
    except Exception as e:
        logger.error(f"Error retrieving business info: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Run the Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') == 'development')