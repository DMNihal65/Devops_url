from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
import random
import string
import uvicorn
from typing import Optional, Dict, Any
import asyncio
import logging
import os
import psycopg2

from database import get_db, URL, create_tables, DATABASE_URL
from cache import get_cache, set_cache, delete_cache, increment_counter
from analytics import send_click_event

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("url-shortener-api")

app = FastAPI(title="URL Shortener API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables on startup
@app.on_event("startup")
def startup_event():
    create_tables()
    # Run migration to add expired column
    try:
        # Connect to the database
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='urls' AND column_name='expired';
        """)
        
        if cursor.fetchone() is None:
            # Add the expired column
            cursor.execute("""
                ALTER TABLE urls 
                ADD COLUMN expired BOOLEAN DEFAULT FALSE;
            """)
            logger.info("Added 'expired' column to urls table")
        else:
            logger.info("Column 'expired' already exists")
            
        # Close connection
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"Error running migration: {e}")

class URLBase(BaseModel):
    target_url: HttpUrl

class URLInfo(BaseModel):
    target_url: str
    short_url: str
    clicks: int

    class Config:
        orm_mode = True

def generate_short_url(length: int = 6) -> str:
    """Generate a random short URL of specified length."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

@app.get("/")
def read_root():
    return {"message": "Welcome to URL Shortener API"}

@app.post("/url", response_model=URLInfo)
def create_url(url: URLBase, db: Session = Depends(get_db)):
    """Create a short URL from a target URL."""
    short_url = generate_short_url()
    
    # Ensure the short URL is unique
    while db.query(URL).filter(URL.short_url == short_url).first():
        short_url = generate_short_url()
    
    # Create new URL record
    db_url = URL(
        target_url=str(url.target_url),
        short_url=short_url,
        clicks=0
    )
    
    # Save to database
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    
    # Cache the URL data
    cache_data = {
        "target_url": db_url.target_url,
        "short_url": db_url.short_url,
        "clicks": db_url.clicks
    }
    set_cache(f"url:{short_url}", cache_data)
    
    return db_url

@app.get("/{short_url}")
async def redirect_to_url(
    short_url: str, 
    request: Request, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Redirect to the target URL for a given short URL."""
    # Try to get URL from cache first
    cached_url = get_cache(f"url:{short_url}")
    
    if cached_url:
        # Increment click count in cache
        increment_counter(f"clicks:{short_url}")
        
        # Send analytics event in the background
        background_tasks.add_task(
            send_click_event,
            short_url=short_url,
            referrer=request.headers.get("referer"),
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host
        )
        
        return {"target_url": cached_url["target_url"]}
    
    # If not in cache, get from database
    db_url = db.query(URL).filter(URL.short_url == short_url).first()
    
    if not db_url:
        raise HTTPException(status_code=404, detail="URL not found")
    
    if db_url.expired:
        raise HTTPException(status_code=410, detail="URL has expired")
    
    # Increment click count
    db_url.clicks += 1
    db.commit()
    
    # Cache the URL data
    cache_data = {
        "target_url": db_url.target_url,
        "short_url": db_url.short_url,
        "clicks": db_url.clicks
    }
    set_cache(f"url:{short_url}", cache_data)
    
    # Send analytics event in the background
    background_tasks.add_task(
        send_click_event,
        short_url=short_url,
        referrer=request.headers.get("referer"),
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host
    )
    
    return {"target_url": db_url.target_url}

@app.get("/stats/{short_url}", response_model=URLInfo)
def get_url_stats(short_url: str, db: Session = Depends(get_db)):
    """Get statistics for a short URL."""
    # Try to get URL from cache first
    cached_url = get_cache(f"url:{short_url}")
    cached_clicks = get_cache(f"clicks:{short_url}")
    
    if cached_url:
        # If we have cached clicks, update the cached URL data
        if cached_clicks:
            cached_url["clicks"] += int(cached_clicks)
        return URLInfo(**cached_url)
    
    # If not in cache, get from database
    db_url = db.query(URL).filter(URL.short_url == short_url).first()
    
    if not db_url:
        raise HTTPException(status_code=404, detail="URL not found")
    
    # Cache the URL data
    cache_data = {
        "target_url": db_url.target_url,
        "short_url": db_url.short_url,
        "clicks": db_url.clicks
    }
    set_cache(f"url:{short_url}", cache_data)
    
    return db_url

@app.post("/sync-cache")
def sync_cache_with_db(db: Session = Depends(get_db)):
    """Synchronize cache click counts with the database."""
    # This would be called periodically by a background task
    # For each URL in the database
    urls = db.query(URL).all()
    for url in urls:
        # Get cached click count
        cached_clicks = get_cache(f"clicks:{url.short_url}")
        if cached_clicks:
            # Update database click count
            url.clicks += int(cached_clicks)
            # Reset cached click count
            delete_cache(f"clicks:{url.short_url}")
    
    # Commit all updates
    db.commit()
    
    return {"message": "Cache synchronized with database"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True) 