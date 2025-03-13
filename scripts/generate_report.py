# Export reviews as CSV/PDF
#!/usr/bin/env python3
import sys
import os
import argparse
import logging
import csv
import json
from datetime import datetime
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import ReviewDatabase
from config import EXPORT_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/generate_report.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def export_csv(place_id, output_file=None):
    """
    Export reviews to CSV
    
    Args:
        place_id (str): Google Places ID
        output_file (str, optional): Output file path
        
    Returns:
        str: Path to the generated CSV file
    """
    try:
        logger.info(f"Exporting reviews to CSV for place ID: {place_id}")
        
        # Initialize database
        db = ReviewDatabase()
        
        # Get business info
        business_info = db.get_business_info(place_id)
        business_name = business_info.get('name', 'Unknown') if business_info else 'Unknown'
        
        # Get reviews
        reviews = db.get_reviews(place_id, limit=10000)
        
        if not reviews:
            logger.warning(f"No reviews found for place ID: {place_id}")
            return None
        
        # Create DataFrame
        data = []
        for review in reviews:
            # Extract sentiment data
            sentiment_data = review.get('sentiment_data', {})
            
            data.append({
                'Review ID': review.get('review_id', ''),
                'Author': review.get('author_name', ''),
                'Rating': review.get('rating', 0),
                'Text': review.get('text', ''),
                'Date': datetime.fromtimestamp(review.get('time', 0)).strftime('%Y-%m-%d'),
                'Sentiment': review.get('sentiment_label', ''),
                'Sentiment Score': review.get('sentiment_score', 0),
                'Positive Score': sentiment_data.get('positive', 0),
                'Negative Score': sentiment_data.get('negative', 0),
                'Neutral Score': sentiment_data.get('neutral', 0),
                'Keywords': ', '.join(review.get('keywords', []))
            })
        
        df = pd.DataFrame(data)
        
        # Generate output file path if not provided
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            business_name_safe = ''.join(c if c.isalnum() else '_' for c in business_name)
            filename = f"{business_name_safe}_{timestamp}.csv"
            output_file = os.path.join(EXPORT_DIR, filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Save to CSV
        df.to_csv(output_file, index=False, quoting=csv.QUOTE_ALL, encoding='utf-8')
        
        logger.info(f"Exported {len(reviews)} reviews to {output_file}")
        return output_file
    
    except Exception as e:
        logger.error(f"Error exporting reviews to CSV: {str(e)}")
        return None

def generate_pdf_report(place_id, output_file=None):
    """
    Generate PDF report for business
    
    Args:
        place_id (str): Google Places ID
        output_file (str, optional): Output file path
        
    Returns:
        str: Path to the generated PDF file
    """
    try:
        logger.info(f"Generating PDF report for place ID: {place_id}")
        
        # Initialize database
        db = ReviewDatabase()
        
        # Get business info
        business_info = db.get_business_info(place_id)
        if not business_info:
            logger.warning(f"No business info found for place ID: {place_id}")
            return None
        
        business_name = business_info.get('name', 'Unknown Business')
        
        # Get review statistics
        stats = db.get_review_stats(place_id)
        
        # Generate output file path if not provided
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            business_name_safe = ''.join(c if c.isalnum() else '_' for c in business_name)
            filename = f"{business_name_safe}_Report_{timestamp}.pdf"
            output_file = os.path.join(EXPORT_DIR, filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Create visualizations using matplotlib
        
        # Set style
        plt.style.use('seaborn-v0_8-whitegrid')
        sns.set_palette("Blues_r")
        
        # Create figure with subplots
        fig = plt.figure(figsize=(11, 8.5))
        
        # Add title
        fig.suptitle(f"Review Analysis: {business_name}", fontsize=16, y=0.98)
        
        # Business info
        ax1 = plt.subplot2grid((3, 3), (0, 0), colspan=3)
        ax1.axis('off')
        info_text = (
            f"Business: {business_info.get('name', 'Unknown')}\n"
            f"Address: {business_info.get('address', 'N/A')}\n"
            f"Phone: {business_info.get('phone', 'N/A')}\n"
            f"Website: {business_info.get('website', 'N/A')}\n"
            f"Overall Rating: {business_info.get('rating', 0)} ({business_info.get('total_ratings', 0)} ratings)\n"
            f"Report Date: {datetime.now().strftime('%Y-%m-%d')}"
        )
        ax1.text(0.02, 0.8, info_text, fontsize=10)
        
        # Rating distribution
        ax2 = plt.subplot2grid((3, 3), (1, 0))
        ratings = stats.get('rating_distribution', {})
        bars = ax2.bar(ratings.keys(), ratings.values())
        ax2.set_title('Rating Distribution')
        ax2.set_xlabel('Rating')
        ax2.set_ylabel('Count')
        for bar in bars:
            height = bar.get_height()
            ax2.annotate(f'{height}', xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points", ha='center', va='bottom')
        
        # Sentiment distribution
        ax3 = plt.subplot2grid((3, 3), (1, 1))
        sentiments = stats.get('sentiment_distribution', {})
        ax3.pie(sentiments.values(), labels=sentiments.keys(), autopct='%1.1f%%',
               startangle=90, colors=['green', 'gray', 'red'])
        ax3.set_title('Sentiment Distribution')
        
        # Time distribution (reviews over time)
        ax4 = plt.subplot2grid((3, 3), (1, 2))
        times = stats.get('time_distribution', {})
        months = list(times.keys())
        counts = list(times.values())
        ax4.plot(months, counts, marker='o')
        ax4.set_title('Reviews Over Time')
        ax4.set_xlabel('Month')
        ax4.set_ylabel('Count')
        plt.xticks(rotation=45)
        
        # Top keywords
        ax5 = plt.subplot2grid((3, 3), (2, 0), colspan=2)
        keywords = stats.get('top_keywords', {})
        if keywords:
            sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10]
            kw_words = [k[0] for k in sorted_keywords]
            kw_counts = [k[1] for k in sorted_keywords]
            y_pos = range(len(kw_words))
            ax5.barh(y_pos, kw_counts)
            ax5.set_yticks(y_pos)
            ax5.set_yticklabels(kw_words)
            ax5.invert_yaxis()  # Labels read top-to-bottom
            ax5.set_title('Top Keywords')
            ax5.set_xlabel('Count')
        else:
            ax5.text(0.5, 0.5, "No keyword data available", horizontalalignment='center')
            ax5.set_title('Top Keywords')
            ax5.axis('off')
        
        # Summary statistics
        ax6 = plt.subplot2grid((3, 3), (2, 2))
        ax6.axis('off')
        summary_text = (
            f"Total Reviews Analyzed: {stats.get('total_reviews', 0)}\n"
            f"Average Rating: {stats.get('average_rating', 0)}\n"
            f"Positive Reviews: {sentiments.get('positive', 0)}\n"
            f"Neutral Reviews: {sentiments.get('neutral', 0)}\n"
            f"Negative Reviews: {sentiments.get('negative', 0)}\n"
        )
        ax6.text(0.05, 0.95, summary_text, verticalalignment='top')
        ax6.set_title('Summary')
        
        # Adjust layout and save figure
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.savefig(output_file)
        plt.close(fig)
        
        logger.info(f"Generated PDF report at {output_file}")
        return output_file
    
    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}")
        return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Generate reports from Google reviews')
    parser.add_argument('place_id', help='Google Places ID for the business')
    parser.add_argument('--format', choices=['csv', 'pdf', 'all'], default='all',
                       help='Report format (csv, pdf, or all)')
    parser.add_argument('--output', help='Output file path')
    args = parser.parse_args()
    
    # Generate reports
    csv_path = None
    pdf_path = None
    
    if args.format in ['csv', 'all']:
        csv_path = export_csv(args.place_id, args.output if args.format == 'csv' else None)
        if csv_path:
            print(f"CSV report generated: {csv_path}")
    
    if args.format in ['pdf', 'all']:
        pdf_path = generate_pdf_report(args.place_id, args.output if args.format == 'pdf' else None)
        if pdf_path:
            print(f"PDF report generated: {pdf_path}")
    
    if not csv_path and not pdf_path:
        print("No reports were generated. Please check the logs for errors.")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())