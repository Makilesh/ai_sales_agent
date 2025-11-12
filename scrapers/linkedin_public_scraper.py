"""
EXPERIMENTAL LinkedIn Public Scraper - NO LOGIN REQUIRED

⚠️ WARNING: This scraper is HIGHLY EXPERIMENTAL and carries significant ban risks.
- LinkedIn actively blocks automated scraping
- Use ONLY for small-scale testing (Phase 1.1 - Lead Discovery)
- Designed to avoid login but may still trigger rate limits
- DO NOT use in production without proper LinkedIn API access
- Always prefer official LinkedIn API when available

Anti-ban measures implemented:
- 2 requests/minute maximum (30+ second delays)
- Random 8-15 second delays between requests
- Rotating user agents (5 desktop variants)
- Only 10 results per keyword (no pagination)
- 403/429/999 errors return empty list (no retries)
- Daily limit: 20 requests
"""

import asyncio
import random
import time
import urllib.parse
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

from models.lead import Lead
from scrapers.base import BaseScraper


class LinkedInPublicScraper(BaseScraper):
    """Experimental scraper for public LinkedIn content without authentication."""
    
    # Class-level request counter for daily limit
    _daily_request_count = 0
    _daily_reset_time = datetime.now()
    
    DAILY_LIMIT = 20
    MAX_RESULTS_PER_KEYWORD = 10
    
    DEFAULT_USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    
    def __init__(
        self,
        keywords: list[str],
        user_agents: list[str] | None = None,
        rate_limit: int = 2  # requests per minute
    ) -> None:
        super().__init__(keywords, rate_limit)
        self.user_agents = user_agents or self.DEFAULT_USER_AGENTS
        self.session = requests.Session()
        
    def _get_random_user_agent(self) -> str:
        """Select random user agent for request."""
        return random.choice(self.user_agents)
    
    def _build_search_headers(self, user_agent: str) -> dict:
        """Build headers for LinkedIn search request."""
        return {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
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
    
    def _is_blocked_response(self, response: requests.Response) -> bool:
        """Check if LinkedIn blocked the request."""
        return response.status_code in [403, 429, 999]
    
    async def _random_delay(self) -> None:
        """Apply random delay between 8-15 seconds."""
        delay = random.uniform(8.0, 15.0)
        await asyncio.sleep(delay)
    
    def _check_daily_limit(self) -> bool:
        """Check if daily request limit has been reached."""
        now = datetime.now()
        
        # Reset counter if new day
        if now.date() > self._daily_reset_time.date():
            LinkedInPublicScraper._daily_request_count = 0
            LinkedInPublicScraper._daily_reset_time = now
        
        return self._daily_request_count < self.DAILY_LIMIT
    
    def _increment_request_count(self) -> None:
        """Increment daily request counter."""
        LinkedInPublicScraper._daily_request_count += 1
    
    async def scrape(self) -> list[Lead]:
        """Scrape public LinkedIn content for all keywords."""
        if not self._check_daily_limit():
            print(f"⚠️  LinkedIn daily limit reached ({self.DAILY_LIMIT} requests). Skipping.")
            return []
        
        all_leads: list[Lead] = []
        
        for keyword in self.keywords[:5]:  # Limit to 5 keywords max
            if not self._check_daily_limit():
                print(f"⚠️  Daily limit reached during scraping. Stopping.")
                break
            
            try:
                print(f"🔍 Searching LinkedIn for: '{keyword}'")
                leads = await self._search_keyword(keyword)
                all_leads.extend(leads)
                
                # Random delay between keywords
                if keyword != self.keywords[-1]:
                    await self._random_delay()
                    
            except Exception as e:
                print(f"⚠️  Error searching LinkedIn for '{keyword}': {e}")
                continue
        
        return all_leads
    
    async def _search_keyword(self, keyword: str) -> list[Lead]:
        """Search LinkedIn for a single keyword."""
        leads: list[Lead] = []
        
        # Build search URL
        encoded_keyword = urllib.parse.quote(keyword)
        search_url = f"https://www.linkedin.com/search/results/content/?keywords={encoded_keyword}&origin=GLOBAL_SEARCH_HEADER&start=0"
        
        # Apply rate limiting
        await self._apply_rate_limit()
        
        # Select random user agent and build headers
        user_agent = self._get_random_user_agent()
        headers = self._build_search_headers(user_agent)
        
        try:
            # Make request in thread to avoid blocking
            print(f"  → Fetching: {search_url[:80]}...")
            response = await asyncio.to_thread(
                self.session.get,
                search_url,
                headers=headers,
                timeout=15
            )
            
            self._increment_request_count()
            
            # Check if blocked
            if self._is_blocked_response(response):
                print(f"  ⚠️  LinkedIn blocked request (status {response.status_code}). Skipping.")
                return []
            
            if response.status_code != 200:
                print(f"  ⚠️  Unexpected status code: {response.status_code}")
                return []
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find search result cards
            result_cards = soup.find_all(['div', 'li'], class_=lambda x: x and (
                'entity-result' in x or 
                'update-components-actor' in x or
                'reusable-search__result' in x or
                'search-result' in x
            ))
            
            print(f"  → Found {len(result_cards)} result cards")
            
            # Parse results (max 10)
            for index, card in enumerate(result_cards[:self.MAX_RESULTS_PER_KEYWORD]):
                try:
                    lead = self._parse_search_result(card, keyword, index)
                    if lead:
                        leads.append(lead)
                except Exception as e:
                    print(f"  ⚠️  Error parsing result {index}: {e}")
                    continue
            
            print(f"  ✓ Extracted {len(leads)} leads from '{keyword}'")
            
        except requests.RequestException as e:
            print(f"  ⚠️  Request failed for '{keyword}': {e}")
        except Exception as e:
            print(f"  ⚠️  Unexpected error for '{keyword}': {e}")
        
        return leads
    
    def _parse_search_result(self, card, keyword: str, index: int) -> Lead | None:
        """Parse a single search result card into a Lead."""
        try:
            # Extract author name
            author_elem = card.find(['span', 'div'], class_=lambda x: x and (
                'entity-result__title-text' in x or
                'update-components-actor__name' in x or
                'actor-name' in x
            ))
            author = author_elem.get_text(strip=True) if author_elem else "LinkedIn User"
            
            # Extract content/snippet
            content_elem = card.find(['p', 'div'], class_=lambda x: x and (
                'entity-result__summary' in x or
                'update-components-text' in x or
                'feed-shared-text' in x
            ))
            content = content_elem.get_text(strip=True) if content_elem else ""
            
            # Extract title
            title_elem = card.find(['a', 'span'], class_=lambda x: x and (
                'app-aware-link' in x or
                'entity-result__title' in x
            ))
            title = title_elem.get_text(strip=True) if title_elem else keyword
            
            # Combine title and content
            full_content = f"{title}\n\n{content}" if content else title
            full_content = full_content[:500]  # Limit to 500 chars
            
            # Extract URL
            link_elem = card.find('a', href=True)
            url = link_elem['href'] if link_elem else f"https://www.linkedin.com/search/results/content/?keywords={urllib.parse.quote(keyword)}"
            
            # Clean URL (remove tracking parameters)
            if '?' in url and not url.startswith('http'):
                url = f"https://www.linkedin.com{url.split('?')[0]}"
            elif not url.startswith('http'):
                url = f"https://www.linkedin.com{url}"
            
            # Extract engagement if visible
            engagement_elem = card.find(['span', 'button'], class_=lambda x: x and 'reaction' in x.lower() if x else False)
            engagement_score = 0
            if engagement_elem:
                engagement_text = engagement_elem.get_text(strip=True)
                # Try to extract number
                import re
                numbers = re.findall(r'\d+', engagement_text)
                if numbers:
                    engagement_score = int(numbers[0])
            
            # Validate content
            if not full_content or len(full_content) < 10:
                return None
            
            return Lead(
                source='linkedin_public',
                author=author,
                content=full_content,
                timestamp=datetime.now(),  # No reliable timestamp in search results
                url=url,
                title=title,
                engagement_score=engagement_score,
                metadata={
                    'search_query': keyword,
                    'result_position': index,
                    'is_public_search': True,
                    'scrape_method': 'public_no_auth'
                }
            )
            
        except Exception as e:
            print(f"    ⚠️  Parse error: {e}")
            return None
    
    def __repr__(self) -> str:
        return f"LinkedInPublicScraper(keywords={len(self.keywords)}, daily_requests={self._daily_request_count}/{self.DAILY_LIMIT})"
