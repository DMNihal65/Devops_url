import httpx
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any

# Analytics service URL
ANALYTICS_URL = "http://analytics:8001/events/click"

async def send_click_event(
    short_url: str,
    referrer: Optional[str] = None,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
    country: Optional[str] = None
) -> None:
    """Send a click event to the analytics service."""
    # Format the timestamp as a string to avoid serialization issues
    current_time = datetime.utcnow().isoformat()
    
    event_data = {
        "short_url": short_url,
        "timestamp": current_time,
        "referrer": referrer or "",
        "user_agent": user_agent or "",
        "ip_address": ip_address or "",
        "country": country or ""
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(ANALYTICS_URL, json=event_data, timeout=2.0)
            if response.status_code >= 400:
                print(f"Error sending analytics event: {response.status_code} - {response.text}")
    except Exception as e:
        # Log the error but don't fail the request
        print(f"Error sending analytics event: {e}") 