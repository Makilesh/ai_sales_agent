"""Lead data model for scraped leads."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any


@dataclass
class Lead:
    """Represents a scraped lead from any platform."""
    
    source: str  # 'reddit', 'discord', 'slack'
    author: str
    content: str
    timestamp: datetime
    url: str
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # Optional fields
    title: str | None = None
    engagement_score: int = 0  # upvotes, reactions, etc.
    channel_name: str | None = None
    subreddit: str | None = None
    
    def __post_init__(self) -> None:
        """Validate lead data after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate required fields and data types."""
        if not self.source:
            raise ValueError("Source cannot be empty")
        
        if self.source not in {'reddit', 'discord', 'slack'}:
            raise ValueError(f"Invalid source: {self.source}")
        
        if not self.author or not self.author.strip():
            raise ValueError("Author cannot be empty")
        
        if not self.content or not self.content.strip():
            raise ValueError("Content cannot be empty")
        
        if len(self.content) > 10000:
            raise ValueError("Content exceeds maximum length of 10000 characters")
        
        if not self.url or not self.url.startswith(('http://', 'https://')):
            raise ValueError("Invalid URL format")
        
        if not isinstance(self.timestamp, datetime):
            raise ValueError("Timestamp must be a datetime object")
    
    def to_dict(self) -> dict[str, Any]:
        """Convert lead to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert datetime to ISO format string
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def matches_keywords(self, keywords: list[str]) -> bool:
        """Check if lead content matches any of the provided keywords."""
        content_lower = self.content.lower()
        title_lower = self.title.lower() if self.title else ""
        
        return any(
            keyword.lower() in content_lower or keyword.lower() in title_lower
            for keyword in keywords
        )
    
    def is_qualified(self, min_engagement: int = 1) -> bool:
        """Check if lead meets basic qualification criteria."""
        return (
            self.engagement_score >= min_engagement
            and len(self.content) >= 20
        )
    
    def __repr__(self) -> str:
        """String representation of the lead."""
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"Lead(source={self.source}, author={self.author}, content='{content_preview}')"
