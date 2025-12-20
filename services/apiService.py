
import os
from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta
from utils.logger import logger

load_dotenv("app.config")
load_dotenv()

def fetch_nasa_events(limit=10, days=365):
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        params = {
            "limit": limit,
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d")
        }
        
        url = os.getenv("NASA_API_URL")
        logger.log(f"API Request: {url} with date range: {start_date} to {end_date}, limit={limit}")
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        events = response.json().get("events", [])
        logger.log(f"API Response: Received {len(events)} events from NASA")
        
        if events:
            dates = [e['geometry'][0]['date'] for e in events if e.get('geometry')]
            if dates:
                date_range = f"{min(dates)} to {max(dates)}"
                logger.log(f"Event date range in results: {date_range}")
        
        return events
    except Exception as e:
        logger.log(f"API Error in fetch_nasa_events: {e}")
        return []

