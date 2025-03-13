# API keys & settings
import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/config.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API keys
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    logger.warning("GOOGLE_API_KEY not found in environment variables")

# Database configuration
DB_PATH = os.getenv('DB_PATH', 'data/reviews.db')

# Web scraping configuration
SCRAPER_TIMEOUT = int(os.getenv('SCRAPER_TIMEOUT', 30))
SCRAPER_DELAY = float(os.getenv('SCRAPER_DELAY', 2.0))

# API configuration
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', 5000))
API_DEBUG = os.getenv('API_DEBUG', 'False').lower() == 'true'

# Frontend configuration
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

# CORS configuration
CORS_ORIGINS = os.getenv('CORS_ORIGINS', FRONTEND_URL).split(',')

# Sentiment analysis configuration
SENTIMENT_THRESHOLD_POSITIVE = float(os.getenv('SENTIMENT_THRESHOLD_POSITIVE', 0.05))
SENTIMENT_THRESHOLD_NEGATIVE = float(os.getenv('SENTIMENT_THRESHOLD_NEGATIVE', -0.05))

# Scheduled tasks configuration
SCHEDULE_ENABLED = os.getenv('SCHEDULE_ENABLED', 'False').lower() == 'true'
SCHEDULE_INTERVAL_HOURS = int(os.getenv('SCHEDULE_INTERVAL_HOURS', 24))

# Export configuration
EXPORT_DIR = os.getenv('EXPORT_DIR', 'data/exports')
os.makedirs(EXPORT_DIR, exist_ok=True)

# Check for required environment variables
def validate_config():
    """Validate the configuration"""
    required_vars = ['GOOGLE_API_KEY']
    missing_vars = [var for var in required_vars if not globals().get(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    return True

# Export configuration as a dictionary
def get_config():
    """Get all configuration as a dictionary"""
    return {
        'GOOGLE_API_KEY': GOOGLE_API_KEY,
        'DB_PATH': DB_PATH,
        'SCRAPER_TIMEOUT': SCRAPER_TIMEOUT,
        'SCRAPER_DELAY': SCRAPER_DELAY,
        'API_HOST': API_HOST,
        'API_PORT': API_PORT,
        'API_DEBUG': API_DEBUG,
        'FRONTEND_URL': FRONTEND_URL,
        'CORS_ORIGINS': CORS_ORIGINS,
        'SENTIMENT_THRESHOLD_POSITIVE': SENTIMENT_THRESHOLD_POSITIVE,
        'SENTIMENT_THRESHOLD_NEGATIVE': SENTIMENT_THRESHOLD_NEGATIVE,
        'SCHEDULE_ENABLED': SCHEDULE_ENABLED,
        'SCHEDULE_INTERVAL_HOURS': SCHEDULE_INTERVAL_HOURS,
        'EXPORT_DIR': EXPORT_DIR
    }