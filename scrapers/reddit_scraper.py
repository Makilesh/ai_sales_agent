"""Reddit scraper implementation."""

import asyncio
from datetime import datetime

import praw
from praw.models import Submission, Comment

from models.lead import Lead
from scrapers.base import BaseScraper


class RedditScraper(BaseScraper):
    """Scraper for Reddit posts and comments."""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str,
        keywords: list[str],
        subreddits: list[str],
        rate_limit: int = 100
    ) -> None:
        super().__init__(keywords, rate_limit)
        self.subreddits = subreddits
        self.skip_keyword_filter = True  # Reddit uses help-seeking subreddits, bypass keyword filter
        
        try:
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            self.reddit.read_only = True
        except Exception as e:
            raise ValueError(f"Failed to initialize Reddit client: {e}")
    
    def _filter_leads(self, leads: list[Lead]) -> list[Lead]:
        """
        Override parent's keyword filtering for Reddit.
        
        Reddit uses help-seeking subreddits, so we trust the subreddit selection
        and let ALL posts through (LLM will filter for service match).
        """
        print(f"   � Reddit: Keyword filter disabled (trusting help-seeking subreddits)")
        return leads  # Return all leads, no keyword filter
    
    async def scrape(self) -> list[Lead]:
        """Scrape posts and comments from specified subreddits."""
        all_leads: list[Lead] = []
        
        for subreddit_name in self.subreddits:
            try:
                leads = await self._scrape_subreddit(subreddit_name)
                all_leads.extend(leads)
            except Exception as e:
                print(f"Error scraping r/{subreddit_name}: {e}")
                continue
        
        return all_leads
    
    async def _scrape_subreddit(self, subreddit_name: str) -> list[Lead]:
        """Scrape a single subreddit for posts and comments."""
        leads: list[Lead] = []
        
        try:
            # Wrap PRAW call in thread executor for true async
            subreddit = await asyncio.to_thread(self.reddit.subreddit, subreddit_name)
            
            # Scrape from multiple feeds for variety
            # Hot posts (current trending)
            hot_posts = await asyncio.to_thread(lambda: list(subreddit.hot(limit=50)))
            # New posts (recent activity)
            new_posts = await asyncio.to_thread(lambda: list(subreddit.new(limit=50)))
            
            # Combine and deduplicate
            all_posts = {post.id: post for post in hot_posts + new_posts}.values()
            
            for submission in all_posts:
                await self._apply_rate_limit()
                
                # Check post
                try:
                    post_lead = self._create_lead_from_post(submission, subreddit_name)
                    if post_lead:
                        leads.append(post_lead)
                except Exception as e:
                    print(f"Error processing post {submission.id}: {e}")
                    continue
                
                # Check comments (increased from 10 to 20)
                try:
                    # Apply rate limit before fetching comments
                    await self._apply_rate_limit()
                    # Wrap blocking PRAW operations in thread executor
                    await asyncio.to_thread(submission.comments.replace_more, limit=0)
                    await self._apply_rate_limit()
                    all_comments = await asyncio.to_thread(submission.comments.list)
                    
                    for comment in all_comments[:20]:  # First 20 comments (increased)
                        if isinstance(comment, Comment):
                            comment_lead = self._create_lead_from_comment(
                                comment, 
                                submission, 
                                subreddit_name
                            )
                            if comment_lead:
                                leads.append(comment_lead)
                except Exception as e:
                    print(f"Error processing comments for {submission.id}: {e}")
                    continue
        
        except Exception as e:
            print(f"Error accessing subreddit r/{subreddit_name}: {e}")
        
        return leads
    
    def _create_lead_from_post(self, submission: Submission, subreddit_name: str) -> Lead | None:
        """Create a Lead object from a Reddit post."""
        try:
            content = f"{submission.title}\n\n{submission.selftext}" if submission.selftext else submission.title
            
            return Lead(
                source='reddit',
                author=str(submission.author) if submission.author else '[deleted]',
                content=content,
                timestamp=datetime.fromtimestamp(submission.created_utc),
                url=f"https://reddit.com{submission.permalink}",
                title=submission.title,
                engagement_score=submission.score,
                subreddit=subreddit_name,
                metadata={
                    'post_id': submission.id,
                    'num_comments': submission.num_comments,
                    'post_type': 'submission',
                    'is_self': submission.is_self
                }
            )
        except Exception as e:
            print(f"Error creating lead from post: {e}")
            return None
    
    def _create_lead_from_comment(
        self, 
        comment: Comment, 
        submission: Submission,
        subreddit_name: str
    ) -> Lead | None:
        """Create a Lead object from a Reddit comment."""
        try:
            if not comment.body or comment.body in ['[deleted]', '[removed]']:
                return None
            
            return Lead(
                source='reddit',
                author=str(comment.author) if comment.author else '[deleted]',
                content=comment.body,
                timestamp=datetime.fromtimestamp(comment.created_utc),
                url=f"https://reddit.com{comment.permalink}",
                title=submission.title,
                engagement_score=comment.score,
                subreddit=subreddit_name,
                metadata={
                    'comment_id': comment.id,
                    'post_id': submission.id,
                    'post_type': 'comment',
                    'parent_post_title': submission.title
                }
            )
        except Exception as e:
            print(f"Error creating lead from comment: {e}")
            return None
    
    def __repr__(self) -> str:
        return f"RedditScraper(subreddits={len(self.subreddits)}, keywords={len(self.keywords)})"
