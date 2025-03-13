# Database interactions
import sqlite3
import json
import logging
import os
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

class ReviewDatabase:
    def __init__(self, db_path='data/reviews.db'):
        """
        Initialize database connection
        
        Args:
            db_path (str): Path to SQLite database file
        """
        self.db_path = db_path
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self._create_tables()
    
    def _get_connection(self):
        """Get a database connection"""
        return sqlite3.connect(self.db_path)
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Create businesses table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS businesses (
                place_id TEXT PRIMARY KEY,
                name TEXT,
                address TEXT,
                phone TEXT,
                website TEXT,
                rating REAL,
                total_ratings INTEGER,
                last_updated INTEGER
            )
            ''')
            
            # Create reviews table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                review_id TEXT,
                place_id TEXT,
                author_name TEXT,
                rating INTEGER,
                text TEXT,
                time INTEGER,
                language TEXT,
                profile_photo_url TEXT,
                sentiment_score REAL,
                sentiment_label TEXT,
                sentiment_data TEXT,
                keywords TEXT,
                UNIQUE(review_id, place_id)
            )
            ''')
            
            # Create statistics table for caching
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                place_id TEXT PRIMARY KEY,
                stats_data TEXT,
                last_updated INTEGER
            )
            ''')
            
            conn.commit()
            logger.info("Database tables created successfully")
        
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
            raise
        
        finally:
            if 'conn' in locals():
                conn.close()
    
    def insert_business_info(self, business_info):
        """
        Insert or update business information
        
        Args:
            business_info (dict): Business information
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            place_id = business_info.get('place_id')
            if not place_id:
                logger.error("No place_id provided for business info")
                return False
            
            # Check if business exists
            cursor.execute('SELECT place_id FROM businesses WHERE place_id = ?', (place_id,))
            exists = cursor.fetchone()
            
            current_time = int(datetime.now().timestamp())
            
            if exists:
                # Update existing business
                cursor.execute('''
                UPDATE businesses SET
                    name = ?,
                    address = ?,
                    phone = ?,
                    website = ?,
                    rating = ?,
                    total_ratings = ?,
                    last_updated = ?
                WHERE place_id = ?
                ''', (
                    business_info.get('name', ''),
                    business_info.get('address', ''),
                    business_info.get('phone', ''),
                    business_info.get('website', ''),
                    business_info.get('rating', 0),
                    business_info.get('total_ratings', 0),
                    current_time,
                    place_id
                ))
            else:
                # Insert new business
                cursor.execute('''
                INSERT INTO businesses (
                    place_id, name, address, phone, website, rating, total_ratings, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    place_id,
                    business_info.get('name', ''),
                    business_info.get('address', ''),
                    business_info.get('phone', ''),
                    business_info.get('website', ''),
                    business_info.get('rating', 0),
                    business_info.get('total_ratings', 0),
                    current_time
                ))
            
            conn.commit()
            return True
        
        except Exception as e:
            logger.error(f"Error inserting business info: {str(e)}")
            return False
        
        finally:
            if 'conn' in locals():
                conn.close()
    
    def insert_reviews(self, reviews, place_id):
        """
        Insert or update reviews for a business
        
        Args:
            reviews (list): List of review dictionaries
            place_id (str): Google Places ID for the business
            
        Returns:
            int: Number of reviews inserted or updated
        """
        if not reviews or not place_id:
            return 0
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            count = 0
            
            for review in reviews:
                review_id = review.get('review_id')
                if not review_id:
                    continue
                
                # Check if review exists
                cursor.execute('SELECT id FROM reviews WHERE review_id = ? AND place_id = ?', 
                              (review_id, place_id))
                exists = cursor.fetchone()
                
                # Process sentiment data
                sentiment_data = review.get('sentiment', {})
                sentiment_label = sentiment_data.get('sentiment', 'neutral')
                sentiment_score = sentiment_data.get('compound_score', 0)
                keywords = json.dumps(review.get('keywords', []))
                
                if exists:
                    # Update existing review
                    cursor.execute('''
                    UPDATE reviews SET
                        author_name = ?,
                        rating = ?,
                        text = ?,
                        time = ?,
                        language = ?,
                        profile_photo_url = ?,
                        sentiment_score = ?,
                        sentiment_label = ?,
                        sentiment_data = ?,
                        keywords = ?
                    WHERE review_id = ? AND place_id = ?
                    ''', (
                        review.get('author_name', ''),
                        review.get('rating', 0),
                        review.get('text', ''),
                        review.get('time', 0),
                        review.get('language', 'en'),
                        review.get('profile_photo_url', ''),
                        sentiment_score,
                        sentiment_label,
                        json.dumps(sentiment_data),
                        keywords,
                        review_id,
                        place_id
                    ))
                else:
                    # Insert new review
                    cursor.execute('''
                    INSERT INTO reviews (
                        review_id, place_id, author_name, rating, text, time, language,
                        profile_photo_url, sentiment_score, sentiment_label, sentiment_data, keywords
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        review_id,
                        place_id,
                        review.get('author_name', ''),
                        review.get('rating', 0),
                        review.get('text', ''),
                        review.get('time', 0),
                        review.get('language', 'en'),
                        review.get('profile_photo_url', ''),
                        sentiment_score,
                        sentiment_label,
                        json.dumps(sentiment_data),
                        keywords
                    ))
                
                count += 1
            
            # Invalidate cached statistics
            cursor.execute('DELETE FROM statistics WHERE place_id = ?', (place_id,))
            
            conn.commit()
            logger.info(f"Inserted or updated {count} reviews for place ID: {place_id}")
            return count
        
        except Exception as e:
            logger.error(f"Error inserting reviews: {str(e)}")
            return 0
        
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_reviews(self, place_id, rating=None, sentiment=None, limit=100, offset=0):
        """
        Get reviews for a business with optional filtering
        
        Args:
            place_id (str): Google Places ID
            rating (int, optional): Filter by rating
            sentiment (str, optional): Filter by sentiment (positive, neutral, negative)
            limit (int): Maximum number of reviews to return
            offset (int): Offset for pagination
            
        Returns:
            list: List of review dictionaries
        """
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build query
            query = 'SELECT * FROM reviews WHERE place_id = ?'
            params = [place_id]
            
            if rating is not None:
                query += ' AND rating = ?'
                params.append(int(rating))
            
            if sentiment is not None:
                query += ' AND sentiment_label = ?'
                params.append(sentiment)
            
            query += ' ORDER BY time DESC LIMIT ? OFFSET ?'
            params.extend([int(limit), int(offset)])
            
            # Execute query
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert rows to dictionaries
            reviews = []
            for row in rows:
                review_dict = dict(row)
                
                # Parse JSON fields
                review_dict['sentiment_data'] = json.loads(review_dict['sentiment_data'])
                review_dict['keywords'] = json.loads(review_dict['keywords'])
                
                # Remove internal ID
                review_dict.pop('id', None)
                
                reviews.append(review_dict)
            
            return reviews
        
        except Exception as e:
            logger.error(f"Error retrieving reviews: {str(e)}")
            return []
        
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_review_stats(self, place_id, use_cache=True):
        """
        Get review statistics for a business
        
        Args:
            place_id (str): Google Places ID
            use_cache (bool): Whether to use cached statistics
            
        Returns:
            dict: Review statistics
        """
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row