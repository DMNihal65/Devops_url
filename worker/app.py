import os
import time
import schedule
import requests
import psycopg2
import redis
import json
import logging
from datetime import datetime, timedelta

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/worker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("url-shortener-worker")

# Environment variables
API_URL = os.getenv("API_URL", "http://api:8000")
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/urlshortener")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
URL_EXPIRY_DAYS = int(os.getenv("URL_EXPIRY_DAYS", "30"))

# Redis client
redis_client = redis.from_url(REDIS_URL)

def connect_to_db():
    """Connect to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(DB_URL)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def check_expired_urls():
    """Check for and handle expired URLs."""
    logger.info("Checking for expired URLs...")
    
    conn = connect_to_db()
    if not conn:
        return
    
    try:
        with conn.cursor() as cur:
            # Calculate expiration date
            expiry_date = datetime.now() - timedelta(days=URL_EXPIRY_DAYS)
            
            # Find expired URLs
            cur.execute(
                "SELECT id, short_url FROM urls WHERE created_at < %s",
                (expiry_date,)
            )
            
            expired_urls = cur.fetchall()
            
            if not expired_urls:
                logger.info("No expired URLs found.")
                return
            
            logger.info(f"Found {len(expired_urls)} expired URLs.")
            
            # Process expired URLs
            for url_id, short_url in expired_urls:
                # Delete from Redis cache
                redis_client.delete(f"url:{short_url}")
                redis_client.delete(f"clicks:{short_url}")
                
                # Mark as expired in database (or delete)
                # Here we're just adding an 'expired' column, but you could delete instead
                cur.execute(
                    "UPDATE urls SET expired = TRUE WHERE id = %s",
                    (url_id,)
                )
            
            conn.commit()
            logger.info(f"Processed {len(expired_urls)} expired URLs.")
    
    except Exception as e:
        logger.error(f"Error checking expired URLs: {e}")
    finally:
        conn.close()

def sync_cache_with_db():
    """Synchronize Redis cache click counts with the database."""
    logger.info("Synchronizing cache with database...")
    
    max_retries = 5
    retry_delay = 10  # seconds
    
    for attempt in range(max_retries):
        try:
            response = requests.post(f"{API_URL}/sync-cache", timeout=5)
            if response.status_code == 200:
                logger.info("Cache synchronized successfully.")
                return
            else:
                logger.error(f"Error synchronizing cache: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling sync-cache endpoint (attempt {attempt+1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("Max retries exceeded. Giving up.")

def run_scheduled_tasks():
    """Run all scheduled tasks."""
    schedule.run_pending()

def main():
    """Main function to set up and run the worker."""
    logger.info("Starting URL Shortener Worker...")
    
    # Schedule tasks
    schedule.every(1).hour.do(sync_cache_with_db)
    schedule.every(1).day.at("00:00").do(check_expired_urls)
    
    # Run tasks immediately on startup
    sync_cache_with_db()
    check_expired_urls()
    
    # Main loop
    while True:
        run_scheduled_tasks()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main() 