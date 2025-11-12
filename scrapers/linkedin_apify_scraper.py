"""
LinkedIn Scraper via Apify API - PROFESSIONAL SOLUTION

This scraper uses Apify's LinkedIn Posts Scraper actor for reliable, account-safe scraping.
- NO risk to your LinkedIn account (uses Apify's infrastructure)
- Professional data extraction service
- Handles authentication, rate limiting, and anti-bot measures
- Requires: Apify API token (free tier: 5,000 credits/month)

Setup:
1. Create free account at https://apify.com
2. Get API token from https://console.apify.com/account/integrations
3. Set APIFY_TOKEN in .env file
4. Install: pip install apify-client

Actor used: apify/linkedin-posts-scraper
Docs: https://apify.com/apify/linkedin-posts-scraper
"""

import asyncio
from datetime import datetime
from typing import Optional

from apify_client import ApifyClient

from models.lead import Lead
from scrapers.base import BaseScraper


class LinkedInApifyScraper(BaseScraper):
    """Professional LinkedIn scraper using Apify API service."""
    
    JOB_POSTING_KEYWORDS = [
        'hiring', 'job opening', "we're hiring", 'join our team',
        'apply now', 'career opportunity', 'now hiring', 'careers',
        'job opportunity', 'seeking candidates', 'vacancy', 
        'position available', 'open position'
    ]
    
    def __init__(
        self,
        apify_token: str,
        keywords: list[str],
        max_posts_per_keyword: int = 20,
        rate_limit: int = 10,  # requests per minute
        actor_id: str = "curious_coder/linkedin-post-search-scraper",
        linkedin_cookie: str = "",
        proxy_config: str = "",
        scrape_posts: bool = True,
        scrape_articles: bool = True,
        scrape_discussions: bool = True,
        scrape_comments: bool = True,
        scrape_reactions: bool = True,
        only_posts: bool = True,
        include_sponsored: bool = False,
        min_reactions: int = 0
    ) -> None:
        """
        Initialize LinkedIn Apify scraper.
        
        Args:
            apify_token: Apify API token
            keywords: Search keywords for LinkedIn posts
            max_posts_per_keyword: Maximum posts to fetch per keyword
            rate_limit: API requests per minute
            actor_id: Apify actor ID to use
            linkedin_cookie: LinkedIn li_at cookie (required by some actors)
            proxy_config: Proxy URL (optional, format: http://user:pass@host:port)
            scrape_posts: Include regular posts
            scrape_articles: Include LinkedIn articles
            scrape_discussions: Include discussion threads
            scrape_comments: Include post comments
            scrape_reactions: Include reaction data
            only_posts: Exclude company updates/ads
            include_sponsored: Include sponsored content
            min_reactions: Minimum reactions to consider
        """
        super().__init__(keywords, rate_limit)
        self.apify_token = apify_token
        self.max_posts_per_keyword = max_posts_per_keyword
        self.actor_id = actor_id
        self.linkedin_cookie = linkedin_cookie
        self.proxy_config = proxy_config
        self.scrape_posts = scrape_posts
        self.scrape_articles = scrape_articles
        self.scrape_discussions = scrape_discussions
        self.scrape_comments = scrape_comments
        self.scrape_reactions = scrape_reactions
        self.only_posts = only_posts
        self.include_sponsored = include_sponsored
        self.min_reactions = min_reactions
        
        # Initialize client first
        self.client = ApifyClient(apify_token)
        
        # Then validate
        if not self._validate_apify_token():
            raise ValueError("Invalid or missing Apify token")
    
    def _validate_apify_token(self) -> bool:
        """Validate that Apify token is present and formatted correctly."""
        if not self.apify_token:
            print("⚠️  Apify token not configured")
            return False
        
        if not self.apify_token.startswith('apify_api_'):
            print("⚠️  Apify token format invalid (should start with 'apify_api_')")
            return False
        
        # Test token by checking account info
        try:
            user = self.client.user().get()
            print(f"✓ Apify token valid (User: {user.get('username', 'Unknown')})")
        except Exception as e:
            print(f"⚠️  Apify token test failed: {e}")
            return False
        
        return True
    
    def _is_job_posting(self, text: str) -> bool:
        """Check if content appears to be a job posting."""
        if not text:
            return False
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.JOB_POSTING_KEYWORDS)
    
    async def scrape(self) -> list[Lead]:
        """Scrape LinkedIn posts via Apify for all keywords."""
        all_leads: list[Lead] = []
        
        print(f"🔍 Starting LinkedIn scraping via Apify (max {self.max_posts_per_keyword} posts/keyword)")
        
        for keyword in self.keywords:
            try:
                await self._apply_rate_limit()
                leads = await self._scrape_keyword(keyword)
                all_leads.extend(leads)
                print(f"  ✓ Extracted {len(leads)} leads from '{keyword}'")
            except Exception as e:
                print(f"  ⚠️  Error scraping '{keyword}': {e}")
                continue
        
        print(f"✓ Total LinkedIn leads collected: {len(all_leads)}")
        return all_leads
    
    async def _scrape_keyword(self, keyword: str) -> list[Lead]:
        """Scrape LinkedIn posts for a single keyword via Apify."""
        leads: list[Lead] = []
        
        print(f"  → Searching LinkedIn for: '{keyword}'")
        
        try:
            # Build LinkedIn search URL for the keyword
            import urllib.parse
            encoded_keyword = urllib.parse.quote(keyword)
            search_url = f"https://www.linkedin.com/search/results/content/?keywords={encoded_keyword}"
            
            # Detect actor type and configure input accordingly
            if 'supreme_coder/linkedin-post' in self.actor_id:
                # supreme_coder actor - No cookies needed, takes URLs
                run_input = {
                    'urls': [search_url],
                    'limit': self.max_posts_per_keyword,
                }
            elif 'curious_coder' in self.actor_id:
                # curious_coder actor - Requires cookies
                run_input = {
                    'urls': [search_url],
                    'maxPosts': self.max_posts_per_keyword,
                }
                
                # Add authentication if provided
                if self.linkedin_cookie:
                    run_input['cookie'] = [{
                        'name': 'li_at',
                        'value': self.linkedin_cookie,
                        'domain': '.linkedin.com'
                    }]
                else:
                    print(f"  ⚠️  WARNING: No LinkedIn cookie provided - actor may fail")
                
                # Add user agent
                run_input['userAgent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                
                # Add proxy
                if self.proxy_config:
                    run_input['proxy'] = self.proxy_config
                else:
                    run_input['proxy'] = {'useApifyProxy': True}
            else:
                # Default/generic actor format
                run_input = {
                    'searches': [keyword],
                    'maxPosts': self.max_posts_per_keyword,
                    'scrapeComments': self.scrape_comments,
                    'scrapeReactions': self.scrape_reactions,
                }
            
            print(f"  → Running Apify actor ({self.actor_id})...")
            if 'supreme_coder' in self.actor_id:
                print(f"     • No cookies required ✓")
                print(f"     • Max posts: {self.max_posts_per_keyword}")
            else:
                print(f"     • Cookie: {'✓ Provided' if self.linkedin_cookie else '✗ Missing'}")
                print(f"     • Proxy: {'✓ Configured' if self.proxy_config else '✓ Using Apify proxy'}")
            print(f"     • Posts: {self.scrape_posts}, Articles: {self.scrape_articles}, Discussions: {self.scrape_discussions}")
            
            # Run Apify actor (blocking call, wrap in thread)
            run = await asyncio.to_thread(
                self.client.actor(self.actor_id).call,
                run_input=run_input
            )
            
            # Fetch results from dataset
            print(f"  → Fetching results from dataset...")
            dataset_items = await asyncio.to_thread(
                self.client.dataset(run['defaultDatasetId']).list_items
            )
            
            # Handle different response formats
            if hasattr(dataset_items, 'items'):
                items = dataset_items.items
            elif isinstance(dataset_items, dict):
                items = dataset_items.get('items', [])
            else:
                items = []
            
            print(f"  → Found {len(items)} items from Apify")
            
            # Parse each item
            for item in items:
                try:
                    # Filter by content type
                    item_type = item.get('type', 'post').lower()
                    
                    if item_type == 'post' and not self.scrape_posts:
                        continue
                    if item_type == 'article' and not self.scrape_articles:
                        continue
                    if item_type in ['discussion', 'thread'] and not self.scrape_discussions:
                        continue
                    
                    # Filter by reaction count
                    reactions_total = item.get('reactions', {}).get('total', 0) if isinstance(item.get('reactions'), dict) else 0
                    likes = item.get('likes', 0) or 0
                    total_reactions = reactions_total + likes
                    
                    if total_reactions < self.min_reactions:
                        continue
                    
                    lead = self._create_lead_from_apify_item(item, keyword)
                    if lead:
                        # Filter out job postings
                        if not self._is_job_posting(lead.content):
                            leads.append(lead)
                        else:
                            print(f"    → Filtered job posting: {lead.title[:50] if lead.title else 'N/A'}...")
                except Exception as e:
                    print(f"    ⚠️  Error parsing item: {e}")
                    continue
        
        except Exception as e:
            print(f"  ⚠️  Apify API error for '{keyword}': {e}")
            return []
        
        return leads
    
    def _create_lead_from_apify_item(self, item: dict, keyword: str) -> Optional[Lead]:
        """Create Lead object from Apify response item."""
        try:
            # Extract author
            author = item.get('authorName', 'LinkedIn User')
            
            # Extract content (try multiple fields)
            content = (
                item.get('text', '') or 
                item.get('commentary', '') or 
                item.get('description', '')
            )
            
            if not content or len(content.strip()) < 10:
                return None
            
            # Extract timestamp
            timestamp_str = item.get('postedAt') or item.get('createdAt')
            if timestamp_str:
                try:
                    # Handle ISO format with timezone
                    if timestamp_str.endswith('Z'):
                        timestamp_str = timestamp_str[:-1] + '+00:00'
                    timestamp = datetime.fromisoformat(timestamp_str)
                except Exception:
                    timestamp = datetime.now()
            else:
                timestamp = datetime.now()
            
            # Extract URL
            url = item.get('postUrl', '') or item.get('url', '')
            if not url:
                # Fallback: construct from post ID if available
                post_id = item.get('postId', '')
                if post_id:
                    url = f"https://www.linkedin.com/feed/update/{post_id}"
                else:
                    return None
            
            # Extract title (may be None for comments)
            title = item.get('title') or item.get('headline')
            
            # Calculate engagement score
            likes = item.get('likes', 0) or 0
            reactions_total = item.get('reactions', {}).get('total', 0) if isinstance(item.get('reactions'), dict) else 0
            engagement_score = likes + reactions_total
            
            # Determine post type
            linkedin_post_type = item.get('type', 'post')  # 'post', 'article', 'video', 'comment'
            
            # Build metadata
            metadata = {
                'search_query': keyword,
                'post_id': item.get('postId'),
                'author_profile': item.get('authorProfileUrl'),
                'comment_count': item.get('commentsCount', 0),
                'via_apify': True,
                'actor': 'apify/linkedin-posts-scraper'
            }
            
            return Lead(
                source='linkedin',
                author=author,
                content=content,
                timestamp=timestamp,
                url=url,
                title=title,
                engagement_score=engagement_score,
                linkedin_post_type=linkedin_post_type,
                metadata=metadata
            )
        
        except Exception as e:
            print(f"    ⚠️  Error creating lead from item: {e}")
            return None
    
    def __repr__(self) -> str:
        content_types = []
        if self.scrape_posts:
            content_types.append('posts')
        if self.scrape_articles:
            content_types.append('articles')
        if self.scrape_discussions:
            content_types.append('discussions')
        
        return (
            f"LinkedInApifyScraper("
            f"keywords={len(self.keywords)}, "
            f"max_posts={self.max_posts_per_keyword}, "
            f"types={'+'.join(content_types)}, "
            f"actor={self.actor_id})"
        )
