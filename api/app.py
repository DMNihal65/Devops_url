from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import random
import string
import uvicorn
from typing import Optional

app = FastAPI(title="URL Shortener API")

# In-memory storage for our URLs (will be replaced with PostgreSQL later)
url_mapping = {}

class URLBase(BaseModel):
    target_url: HttpUrl

class URLInfo(URLBase):
    short_url: str
    clicks: int = 0

def generate_short_url(length: int = 6) -> str:
    """Generate a random short URL of specified length."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

@app.get("/")
def read_root():
    return {"message": "Welcome to URL Shortener API"}

@app.post("/url", response_model=URLInfo)
def create_url(url: URLBase):
    """Create a short URL from a target URL."""
    short_url = generate_short_url()
    
    # Ensure the short URL is unique
    while short_url in url_mapping:
        short_url = generate_short_url()
    
    url_info = URLInfo(
        target_url=url.target_url,
        short_url=short_url
    )
    
    url_mapping[short_url] = url_info
    
    return url_info

@app.get("/{short_url}")
def redirect_to_url(short_url: str):
    """Redirect to the target URL for a given short URL."""
    if short_url not in url_mapping:
        raise HTTPException(status_code=404, detail="URL not found")
    
    url_info = url_mapping[short_url]
    url_info.clicks += 1
    
    return {"target_url": url_info.target_url}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True) 