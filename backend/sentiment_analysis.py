# NLP-based sentiment analysis
import re
import nltk
import logging
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from textblob import TextBlob

# Configure logging
logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        # Download required NLTK resources
        try:
            nltk.download('vader_lexicon', quiet=True)
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            
            self.vader = SentimentIntensityAnalyzer()
            self.stopwords = set(stopwords.words('english'))
            logger.info("Sentiment analyzer initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing sentiment analyzer: {str(e)}")
            raise
    
    def preprocess_text(self, text):
        """
        Preprocess text for sentiment analysis
        
        Args:
            text (str): Review text
            
        Returns:
            str: Preprocessed text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Remove HTML tags
        text = re.sub(r'<.*?>', '', text)
        
        # Remove punctuation
        text = re.sub(r'[^\w\s]', '', text)
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords
        tokens = [token for token in tokens if token not in self.stopwords]
        
        # Join tokens back into string
        preprocessed_text = ' '.join(tokens)
        
        return preprocessed_text
    
    def analyze_text(self, text):
        """
        Analyze sentiment of review text
        
        Args:
            text (str): Review text
            
        Returns:
            dict: Sentiment analysis results
        """
        if not text or len(text.strip()) == 0:
            return {
                'sentiment': 'neutral',
                'compound_score': 0,
                'positive': 0,
                'neutral': 1,
                'negative': 0
            }
        
        try:
            # Preprocess text
            preprocessed_text = self.preprocess_text(text)
            
            # Use VADER for sentiment intensity
            vader_scores = self.vader.polarity_scores(preprocessed_text)
            
            # Use TextBlob for additional analysis
            blob = TextBlob(preprocessed_text)
            
            # Determine sentiment label
            compound_score = vader_scores['compound']
            if compound_score >= 0.05:
                sentiment = 'positive'
            elif compound_score <= -0.05:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            # Combine analyses
            result = {
                'sentiment': sentiment,
                'compound_score': compound_score,
                'positive': vader_scores['pos'],
                'neutral': vader_scores['neu'],
                'negative': vader_scores['neg'],
                'subjectivity': blob.sentiment.subjectivity
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return {
                'sentiment': 'neutral',
                'compound_score': 0,
                'positive': 0,
                'neutral': 1,
                'negative': 0,
                'subjectivity': 0
            }
    
    def extract_keywords(self, text, top_n=5):
        """
        Extract key phrases and topics from review text
        
        Args:
            text (str): Review text
            top_n (int): Number of keywords to extract
            
        Returns:
            list: Top keywords
        """
        if not text or len(text.strip()) == 0:
            return []
        
        try:
            # Preprocess text
            preprocessed_text = self.preprocess_text(text)
            
            # Tokenize
            tokens = word_tokenize(preprocessed_text)
            
            # Remove stopwords and short words
            tokens = [token for token in tokens if token not in self.stopwords and len(token) > 2]
            
            # Count frequencies
            freq_dist = nltk.FreqDist(tokens)
            
            # Get top keywords
            keywords = [word for word, _ in freq_dist.most_common(top_n)]
            
            return keywords
        
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            return []
    
    def batch_analyze(self, reviews):
        """
        Analyze sentiment for a batch of reviews
        
        Args:
            reviews (list): List of review dictionaries with 'text' field
            
        Returns:
            dict: Dictionary mapping review IDs to sentiment results
        """
        results = {}
        
        for review in reviews:
            review_id = review.get('review_id')
            text = review.get('text', '')
            
            if review_id and text:
                results[review_id] = self.analyze_text(text)
        
        return results