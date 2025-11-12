"""Anti-detection utilities for public LinkedIn scraping."""

import random
import re
from datetime import datetime, timedelta

import requests


def get_linkedin_user_agents() -> list[str]:
    """
    Returns realistic 2024-2025 desktop user agents.
    
    Returns:
        List of 5 modern desktop user agent strings
    """
    return [
        # Chrome 120+ on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        # Chrome 120+ on macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        # Firefox 121+ on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        # Safari 17+ on macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        # Chrome 120+ on Linux
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]


def get_random_delay(min_sec: float = 8.0, max_sec: float = 15.0) -> float:
    """
    Returns random delay for human-like behavior.
    
    Args:
        min_sec: Minimum delay in seconds
        max_sec: Maximum delay in seconds
        
    Returns:
        Random float between min_sec and max_sec
    """
    return random.uniform(min_sec, max_sec)


def build_linkedin_headers(user_agent: str) -> dict:
    """
    Build complete headers for LinkedIn requests.
    
    Args:
        user_agent: User agent string
        
    Returns:
        Dictionary of HTTP headers
    """
    return {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }


def is_linkedin_blocked(response: requests.Response) -> bool:
    """
    Check if LinkedIn blocked the request.
    
    Args:
        response: requests.Response object
        
    Returns:
        True if blocked, False otherwise
    """
    # Check status codes
    if response.status_code in [403, 429, 999]:
        return True
    
    # Check for auth wall redirect
    if '/authwall' in response.url or '/uas/login' in response.url:
        return True
    
    # Check response body for block indicators
    try:
        body_text = response.text.lower()
        block_indicators = ['captcha', 'security check', 'unusual activity']
        if any(indicator in body_text for indicator in block_indicators):
            return True
    except Exception:
        pass
    
    return False


def parse_relative_time(time_str: str) -> datetime:
    """
    Convert LinkedIn relative time strings to datetime.
    
    Args:
        time_str: Relative time string (e.g., "2h ago", "3d ago", "1w ago")
        
    Returns:
        datetime object (falls back to now() if parsing fails)
    """
    if not time_str:
        return datetime.now()
    
    try:
        # Normalize string
        time_str = time_str.lower().strip()
        
        # Match patterns like "2h", "3d", "1w", "2 hours", "3 days"
        match = re.search(r'(\d+)\s*([smhdwy])', time_str)
        
        if not match:
            return datetime.now()
        
        value = int(match.group(1))
        unit = match.group(2)
        
        # Calculate timedelta
        now = datetime.now()
        
        if unit in ['s', 'sec']:
            return now - timedelta(seconds=value)
        elif unit in ['m', 'min']:
            return now - timedelta(minutes=value)
        elif unit in ['h', 'hour']:
            return now - timedelta(hours=value)
        elif unit in ['d', 'day']:
            return now - timedelta(days=value)
        elif unit in ['w', 'week']:
            return now - timedelta(weeks=value)
        elif unit in ['y', 'year']:
            return now - timedelta(days=value * 365)
        else:
            return now
            
    except Exception:
        return datetime.now()
