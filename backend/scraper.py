# Fetch reviews from Google API or scraping
import os
import time
import requests
import json
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from config import GOOGLE_API_KEY

logger = logging.getLogger(__name__)

class GoogleReviewScraper:
    def __init__(self):
        self.api_key = GOOGLE_API_KEY
    
    def fetch_reviews(self, place_id, max_reviews=100):
        """
        Fetches reviews for a business using either Google Places API or web scraping
        
        Args:
            place_id (str): Google Places ID for the business
            max_reviews (int): Maximum number of reviews to fetch
            
        Returns:
            list: List of review dictionaries
        """
        logger.info(f"Fetching reviews for place ID: {place_id}")
        
        # Try using Google Places API first
        try:
            return self._fetch_reviews_api(place_id, max_reviews)
        except Exception as e:
            logger.warning(f"API fetching failed: {str(e)}. Falling back to web scraping.")
            return self._fetch_reviews_scraping(place_id, max_reviews)
    
    def _fetch_reviews_api(self, place_id, max_reviews):
        """Fetch reviews using Google Places API"""
        if not self.api_key:
            raise ValueError("Google API key is not configured")
        
        reviews = []
        next_page_token = None
        
        while len(reviews) < max_reviews:
            # Build URL for the Places API
            url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=reviews&key={self.api_key}"
            
            if next_page_token:
                url += f"&pagetoken={next_page_token}"
            
            # Make API request
            response = requests.get(url)
            if response.status_code != 200:
                logger.error(f"API returned status code {response.status_code}")
                raise Exception(f"Failed to fetch reviews: HTTP {response.status_code}")
            
            data = response.json()
            
            # Check if the API returned an error
            if data.get('status') != 'OK':
                logger.error(f"API returned error: {data.get('status')}")
                raise Exception(f"API error: {data.get('status')} - {data.get('error_message', '')}")
            
            # Extract reviews
            new_reviews = data.get('result', {}).get('reviews', [])
            
            # Process reviews
            for review in new_reviews:
                reviews.append({
                    'review_id': review.get('time'),  # Using timestamp as unique ID
                    'author_name': review.get('author_name'),
                    'rating': review.get('rating'),
                    'text': review.get('text'),
                    'time': review.get('time'),
                    'language': review.get('language', 'en'),
                    'profile_photo_url': review.get('profile_photo_url', '')
                })
                
                if len(reviews) >= max_reviews:
                    break
            
            # Get next page token if available
            next_page_token = data.get('next_page_token')
            
            # Break if there are no more pages
            if not next_page_token or len(new_reviews) == 0:
                break
            
            # Wait a short time before making the next request
            time.sleep(2)
        
        logger.info(f"Fetched {len(reviews)} reviews using API")
        return reviews
    
    def _fetch_reviews_scraping(self, place_id, max_reviews):
        """Fetch reviews using web scraping (fallback method)"""
        reviews = []
        
        try:
            # Configure Chrome options for headless browsing
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            # Initialize the driver
            driver = webdriver.Chrome(options=chrome_options)
            
            # Navigate to Google Maps page
            map_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
            driver.get(map_url)
            
            # Wait for the page to load
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='main']"))
            )
            
            # Find and click on the reviews tab
            try:
                reviews_tab = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'reviews')]"))
                )
                reviews_tab.click()
                
                # Wait for reviews to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'review')]"))
                )
                
                # Scroll to load more reviews
                last_count = 0
                while len(reviews) < max_reviews:
                    # Scroll down
                    driver.execute_script("document.querySelector('div[role=\"feed\"]').scrollTop += 1000")
                    time.sleep(2)
                    
                    # Extract reviews
                    review_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'review')]")
                    
                    # Break if no new reviews are loaded
                    if len(review_elements) == last_count:
                        break
                    
                    last_count = len(review_elements)
                    
                    # Process new reviews
                    for element in review_elements[len(reviews):]:
                        try:
                            author = element.find_element(By.XPATH, ".//div[contains(@class, 'author')]").text
                            try:
                                rating = len(element.find_elements(By.XPATH, ".//span[contains(@aria-label, 'stars')]")))
                            except:
                                rating = 0
                            
                            try:
                                text = element.find_element(By.XPATH, ".//span[contains(@class, 'review-text')]").text
                            except:
                                text = ""
                            
                            reviews.append({
                                'review_id': f"scrape_{len(reviews)}",
                                'author_name': author,
                                'rating': rating,
                                'text': text,
                                'time': int(time.time()),
                                'language': 'en',  # Default assumption
                                'profile_photo_url': ''
                            })
                            
                            if len(reviews) >= max_reviews:
                                break
                        except Exception as e:
                            logger.warning(f"Error extracting review data: {str(e)}")
                            continue
            
            except Exception as e:
                logger.error(f"Error navigating to reviews tab: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error during web scraping: {str(e)}")
        
        finally:
            if 'driver' in locals():
                driver.quit()
        
        logger.info(f"Fetched {len(reviews)} reviews using web scraping")
        return reviews
    
    def get_business_info(self, place_id):
        """
        Get basic information about a business
        
        Args:
            place_id (str): Google Places ID
            
        Returns:
            dict: Business information
        """
        if not self.api_key:
            raise ValueError("Google API key is not configured")
        
        url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,formatted_address,formatted_phone_number,rating,user_ratings_total,website&key={self.api_key}"
        
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch business info: HTTP {response.status_code}")
        
        data = response.json()
        
        if data.get('status') != 'OK':
            raise Exception(f"API error: {data.get('status')} - {data.get('error_message', '')}")
        
        result = data.get('result', {})
        
        return {
            'name': result.get('name', ''),
            'address': result.get('formatted_address', ''),
            'phone': result.get('formatted_phone_number', ''),
            'website': result.get('website', ''),
            'rating': result.get('rating', 0),
            'total_ratings': result.get('user_ratings_total', 0)
        }