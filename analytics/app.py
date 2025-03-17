from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
import uvicorn
from datetime import datetime
import os
import logging

from database import get_db, ClickEvent, create_tables

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/analytics.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("url-shortener-analytics")

app = FastAPI(title="URL Shortener Analytics Service")

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

class ClickEventCreate(BaseModel):
    short_url: str
    timestamp: datetime = None
    referrer: str = None
    user_agent: str = None
    ip_address: str = None
    country: str = None

class ClickEventResponse(BaseModel):
    id: int
    short_url: str
    timestamp: datetime
    referrer: str = None
    user_agent: str = None
    ip_address: str = None
    country: str = None

    class Config:
        orm_mode = True

@app.get("/")
def read_root():
    return {"message": "Welcome to URL Shortener Analytics Service"}

def record_click_event(event: ClickEventCreate, db: Session):
    """Background task to record a click event."""
    db_event = ClickEvent(
        short_url=event.short_url,
        timestamp=event.timestamp or datetime.utcnow(),
        referrer=event.referrer,
        user_agent=event.user_agent,
        ip_address=event.ip_address,
        country=event.country
    )
    db.add(db_event)
    db.commit()

@app.post("/events/click", status_code=202)
async def create_click_event(
    event: ClickEventCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Record a click event asynchronously."""
    background_tasks.add_task(record_click_event, event, db)
    return {"message": "Event received"}

@app.get("/analytics/{short_url}", response_model=list[ClickEventResponse])
def get_url_analytics(short_url: str, db: Session = Depends(get_db)):
    """Get analytics for a specific short URL."""
    events = db.query(ClickEvent).filter(ClickEvent.short_url == short_url).all()
    return events

@app.get("/analytics/{short_url}/summary")
def get_url_analytics_summary(short_url: str, db: Session = Depends(get_db)):
    """Get a summary of analytics for a specific short URL."""
    total_clicks = db.query(ClickEvent).filter(ClickEvent.short_url == short_url).count()
    
    # Get unique IP addresses (approximate unique visitors)
    unique_ips = db.query(ClickEvent.ip_address).filter(
        ClickEvent.short_url == short_url
    ).distinct().count()
    
    # Get referrer breakdown
    referrers = db.query(ClickEvent.referrer, func.count(ClickEvent.id)).filter(
        ClickEvent.short_url == short_url
    ).group_by(ClickEvent.referrer).all()
    
    # Get country breakdown
    countries = db.query(ClickEvent.country, func.count(ClickEvent.id)).filter(
        ClickEvent.short_url == short_url
    ).group_by(ClickEvent.country).all()
    
    return {
        "total_clicks": total_clicks,
        "unique_visitors": unique_ips,
        "referrers": dict(referrers),
        "countries": dict(countries)
    }

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True) 