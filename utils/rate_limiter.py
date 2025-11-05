"""Enhanced rate limiting utilities for API scrapers."""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Any


@dataclass
class RateLimiter:
    """
    Token bucket rate limiter for API requests.
    
    More flexible than simple delay-based limiting:
    - Allows burst requests up to max_tokens
    - Refills tokens over time
    - Better handles variable request patterns
    """
    
    max_tokens: int  # Maximum tokens (requests) allowed
    refill_rate: float  # Tokens added per second
    tokens: float = field(init=False)
    last_refill: float = field(init=False)
    
    def __post_init__(self):
        """Initialize with full token bucket."""
        self.tokens = float(self.max_tokens)
        self.last_refill = time.time()
    
    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Add tokens based on refill rate
        self.tokens = min(
            self.max_tokens,
            self.tokens + (elapsed * self.refill_rate)
        )
        self.last_refill = now
    
    async def acquire(self, tokens: int = 1) -> None:
        """
        Acquire tokens, waiting if necessary.
        
        Args:
            tokens: Number of tokens to acquire (default: 1)
        """
        while True:
            self._refill_tokens()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return
            
            # Calculate wait time needed
            tokens_needed = tokens - self.tokens
            wait_time = tokens_needed / self.refill_rate
            await asyncio.sleep(wait_time)
    
    @classmethod
    def from_rate_limit(cls, requests_per_minute: int) -> 'RateLimiter':
        """
        Create rate limiter from requests per minute.
        
        Args:
            requests_per_minute: Maximum requests per minute
            
        Returns:
            Configured RateLimiter instance
        """
        return cls(
            max_tokens=requests_per_minute,
            refill_rate=requests_per_minute / 60.0
        )
    
    @classmethod
    def from_rate_limit_per_second(cls, requests_per_second: int) -> 'RateLimiter':
        """
        Create rate limiter from requests per second.
        
        Args:
            requests_per_second: Maximum requests per second
            
        Returns:
            Configured RateLimiter instance
        """
        return cls(
            max_tokens=requests_per_second * 10,  # Allow small bursts
            refill_rate=float(requests_per_second)
        )


@dataclass
class AdaptiveRateLimiter:
    """
    Rate limiter that adapts to API responses.
    
    Slows down when hitting rate limits, speeds up when succeeding.
    Useful for APIs with variable or unclear rate limits.
    """
    
    initial_delay: float = 1.0  # Initial delay between requests
    min_delay: float = 0.1  # Minimum delay
    max_delay: float = 60.0  # Maximum delay
    backoff_factor: float = 2.0  # Multiply delay on rate limit
    success_factor: float = 0.9  # Multiply delay on success
    
    current_delay: float = field(init=False)
    last_request: float = field(init=False)
    
    def __post_init__(self):
        """Initialize with default values."""
        self.current_delay = self.initial_delay
        self.last_request = 0.0
    
    async def acquire(self) -> None:
        """Wait before making next request."""
        now = time.time()
        elapsed = now - self.last_request
        
        if elapsed < self.current_delay:
            wait_time = self.current_delay - elapsed
            await asyncio.sleep(wait_time)
        
        self.last_request = time.time()
    
    def report_success(self) -> None:
        """Report successful request - speeds up future requests."""
        self.current_delay = max(
            self.min_delay,
            self.current_delay * self.success_factor
        )
    
    def report_rate_limit(self) -> None:
        """Report rate limit hit - slows down future requests."""
        self.current_delay = min(
            self.max_delay,
            self.current_delay * self.backoff_factor
        )
    
    def report_error(self) -> None:
        """Report error - moderately slows down."""
        self.current_delay = min(
            self.max_delay,
            self.current_delay * 1.5
        )


async def rate_limited(
    func: Callable,
    rate_limiter: RateLimiter,
    *args,
    **kwargs
) -> Any:
    """
    Execute function with rate limiting.
    
    Args:
        func: Function to execute
        rate_limiter: RateLimiter instance
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func
        
    Returns:
        Result of func
    """
    await rate_limiter.acquire()
    return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
