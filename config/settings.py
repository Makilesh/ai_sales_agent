"""Configuration settings for Multi-Source Lead Scraping Engine."""

from dataclasses import dataclass, field
from decouple import config


@dataclass
class RedditConfig:
    """Reddit API configuration."""
    client_id: str = config("REDDIT_CLIENT_ID", default="")
    client_secret: str = config("REDDIT_CLIENT_SECRET", default="")
    user_agent: str = config("REDDIT_USER_AGENT", default="LeadScrapingBot/1.0")
    rate_limit: int = 60  # requests per minute (PRAW default)
    subreddits: list[str] = field(default_factory=lambda: [
        # "artificial",
        # "ArtificialIntelligence",
        "rwa"
        "ArtificialIntelligence"
        # "smallbusiness",
        # "SaaS"
    ])


@dataclass
class DiscordConfig:
    """Discord API configuration."""
    bot_token: str = config("DISCORD_BOT_TOKEN", default="")
    rate_limit: int = 50  # requests per second
    channels: list[str] = field(default_factory=lambda: [
        # Add your Discord channel IDs here
        # How to get: Right-click any channel → "Copy Channel ID"
        
        "1118264005207793674",  # Perplexity: #ask-community
        # Add more channel IDs here if needed:
        # "another_channel_id",  # Example: another channel
    ])  # Channel IDs to monitor
    guilds: list[str] = field(default_factory=list)  # Guild IDs to monitor (optional)


@dataclass
class SlackConfig:
    """Slack API configuration."""
    bot_token: str = config("SLACK_BOT_TOKEN", default="")
    app_token: str = config("SLACK_APP_TOKEN", default="")
    rate_limit: int = 1  # requests per second (Tier 1 = 1/sec, Tier 2+ = 100-20k/min)
    channels: list[str] = field(default_factory=list)  # Channel IDs to monitor
    workspaces: list[str] = field(default_factory=list)  # Workspace IDs


@dataclass
class LinkedInPublicConfig:
    """EXPERIMENTAL: LinkedIn public scraping (no login, high ban risk)."""
    enabled: bool = config("LINKEDIN_PUBLIC_ENABLED", default=False, cast=bool)
    rate_limit: int = 2  # requests per minute (NEVER increase)
    max_results_per_keyword: int = 10  # Single page only
    max_daily_requests: int = 20  # Hard daily limit
    delay_min_seconds: float = 8.0
    delay_max_seconds: float = 15.0


@dataclass
class LinkedInApifyConfig:
    """LinkedIn scraping via Apify API (production-ready, no account risk)."""
    enabled: bool = config("LINKEDIN_APIFY_ENABLED", default=False, cast=bool)
    apify_token: str = config("APIFY_TOKEN", default="")
    actor_id: str = config("LINKEDIN_APIFY_ACTOR", default="supreme_coder/linkedin-post")
    max_posts_per_keyword: int = 50
    rate_limit: int = 10  # Apify API calls per minute
    
    # LinkedIn authentication (required by some actors)
    linkedin_cookie: str = config("LINKEDIN_COOKIE", default="")  # li_at cookie value
    proxy_config: str = config("LINKEDIN_PROXY", default="")  # Optional proxy URL
    
    # Content type configuration
    scrape_posts: bool = True  # Regular LinkedIn posts
    scrape_articles: bool = True  # LinkedIn articles
    scrape_discussions: bool = True  # Discussion threads
    scrape_comments: bool = True  # Post comments
    scrape_reactions: bool = True  # Like/reaction data
    
    # Filtering options
    only_posts: bool = True  # Exclude company updates/ads
    include_sponsored: bool = False  # Include sponsored content
    min_reactions: int = 0  # Minimum reactions to consider


@dataclass
class ScrapingConfig:
    """General scraping parameters - SERVICE INQUIRY FOCUSED."""
    
    # ===================================================================
    # SERVICE-BASED KEYWORD PRESETS - For efficient, targeted scraping
    # ===================================================================
    # Use --service flag to select which preset to use
    # Example: python main.py --sources linkedin_apify --service rwa
    
    KEYWORD_PRESETS = {
        'rwa': [
            # RWA-specific keywords (3 keywords = 87% credit savings vs 'all')
            "tokenize real estate",
            "rwa tokenization", 
            "asset tokenization",
            "real world asset blockchain",
            "tokenizing physical assets",
            "rwa platform recommendation"
        ],
        'crypto': [
            # Crypto/Web3 keywords
            "crypto integration",
            "web3 development", 
            "smart contract help",
            "blockchain solution",
            "defi platform recommendation",
            "cryptocurrency payment gateway"
        ],
        'ai': [
            # AI/ML keywords
            "ai automation solution",
            "machine learning consultant",
            "chatbot development service",
            "ai integration help",
            "ml model deployment"
        ],
        'blockchain': [
            # General blockchain keywords
            "blockchain consultant",
            "distributed ledger solution",
            "blockchain integration",
            "smart contract audit"
        ],
        'general': [
            # High-intent service requests (any industry)
            "recommend a tool for",
            "recommend a service for",
            "best solution for",
            "need help with",
            "looking to outsource",
            "want to outsource",
            "need consultant for",
            "seeking expert in",
            "looking for agency",
            "struggling with",
            "how to automate"
        ],
        'all': [
            # ALL keywords - use only when you need comprehensive coverage
            # WARNING: Uses most credits (24 keywords)
            "recommend a tool for",
            "recommend a service for",
            "best solution for",
            "need help with",
            "any tips for",
            "how do I",
            "help me with",
            "looking to outsource",
            "want to outsource",
            "need to outsource",
            "looking for consultant",
            "need consultant for",
            "seeking expert in",
            "looking for agency",
            "struggling with",
            "frustrated by",
            "how to automate",
            "reduce costs on",
            "improve our",
            "scale our",
            "tokenize real estate",
            "rwa tokenization",
            "asset tokenization",
            "crypto integration",
            "web3 development",
            "smart contract help",
            "blockchain solution"
        ]
    }
    
    # Default keywords (used if --service not specified)
    keywords: list[str] = field(default_factory=lambda: [
        # Default: RWA-focused (most efficient for your use case)
        "tokenize real estate",
        "rwa tokenization",
        "asset tokenization",
        
        # # Crypto-specific
        # "crypto integration",
        # "web3 development",
        # "smart contract help",
        # "blockchain solution"
    ])
    
    max_results_per_source: int = 100
    max_total_leads: int = 200  # Global limit - stops scraping after this many total leads
    scrape_interval_seconds: int = 300  # 5 minutes
    enable_sentiment_filter: bool = True
    min_engagement_score: int = 0  # minimum upvotes/reactions (0 = allow posts with no engagement)


@dataclass
class AppSettings:
    """Main application settings."""
    reddit: RedditConfig = field(default_factory=RedditConfig)
    discord: DiscordConfig = field(default_factory=DiscordConfig)
    slack: SlackConfig = field(default_factory=SlackConfig)
    linkedin_public: LinkedInPublicConfig = field(default_factory=LinkedInPublicConfig)
    linkedin_apify: LinkedInApifyConfig = field(default_factory=LinkedInApifyConfig)
    scraping: ScrapingConfig = field(default_factory=ScrapingConfig)
    debug_mode: bool = config("DEBUG", default=False, cast=bool)
    log_level: str = config("LOG_LEVEL", default="INFO")

    def validate(self) -> bool:
        """Validate that required credentials are present."""
        valid = True
        if not self.reddit.client_id or not self.reddit.client_secret:
            print("Warning: Reddit credentials not configured")
            valid = False
        if not self.discord.bot_token:
            print("Warning: Discord bot token not configured")
            valid = False
        if not self.slack.bot_token or not self.slack.app_token:
            print("Warning: Slack credentials not configured")
            valid = False
        if self.linkedin_public.enabled:
            print("⚠️  LinkedIn Public: EXPERIMENTAL - High ban risk. Consider Apify for production.")
        if self.linkedin_apify.enabled and not self.linkedin_apify.apify_token:
            print("Warning: LinkedIn Apify enabled but token not configured")
        return valid


# Global settings instance
settings = AppSettings()
