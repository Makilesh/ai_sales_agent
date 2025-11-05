"""Main entry point for Multi-Source Lead Scraping Engine."""

import argparse
import asyncio
from datetime import datetime
from pathlib import Path

from config.settings import settings
from models.lead import Lead
from scrapers.reddit_scraper import RedditScraper
from scrapers.discord_scraper import DiscordScraper
from scrapers.slack_scraper import SlackScraper
from storage.json_handler import append_leads, save_leads


async def scrape_reddit() -> list[Lead]:
    """Scrape leads from Reddit."""
    print("\n=== Starting Reddit scraping ===")
    try:
        scraper = RedditScraper(
            client_id=settings.reddit.client_id,
            client_secret=settings.reddit.client_secret,
            user_agent=settings.reddit.user_agent,
            keywords=settings.scraping.keywords,
            subreddits=settings.reddit.subreddits,
            rate_limit=settings.reddit.rate_limit
        )
        leads = await scraper.scrape_with_rate_limit()
        print(f"✓ Reddit: Found {len(leads)} leads")
        return leads
    except Exception as e:
        print(f"✗ Reddit scraping failed: {e}")
        return []


async def scrape_discord() -> list[Lead]:
    """Scrape leads from Discord."""
    print("\n=== Starting Discord scraping ===")
    try:
        scraper = DiscordScraper(
            bot_token=settings.discord.bot_token,
            keywords=settings.scraping.keywords,
            channel_ids=settings.discord.channels,
            rate_limit=settings.discord.rate_limit
        )
        leads = await scraper.scrape_with_rate_limit()
        print(f"✓ Discord: Found {len(leads)} leads")
        return leads
    except Exception as e:
        print(f"✗ Discord scraping failed: {e}")
        return []


async def scrape_slack() -> list[Lead]:
    """Scrape leads from Slack."""
    print("\n=== Starting Slack scraping ===")
    try:
        scraper = SlackScraper(
            bot_token=settings.slack.bot_token,
            keywords=settings.scraping.keywords,
            channel_ids=settings.slack.channels,
            rate_limit=settings.slack.rate_limit
        )
        leads = await scraper.scrape_with_rate_limit()
        print(f"✓ Slack: Found {len(leads)} leads")
        return leads
    except Exception as e:
        print(f"✗ Slack scraping failed: {e}")
        return []


async def run_scrapers(sources: list[str]) -> list[Lead]:
    """Run specified scrapers concurrently."""
    tasks = []
    
    if 'reddit' in sources:
        tasks.append(scrape_reddit())
    
    if 'discord' in sources:
        tasks.append(scrape_discord())
    
    if 'slack' in sources:
        tasks.append(scrape_slack())
    
    if not tasks:
        print("No valid sources specified")
        return []
    
    # Run all scrapers concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Flatten results and filter out errors
    all_leads = []
    for result in results:
        if isinstance(result, list):
            all_leads.extend(result)
        elif isinstance(result, Exception):
            print(f"Scraper error: {result}")
    
    return all_leads


def filter_qualified_leads(leads: list[Lead]) -> list[Lead]:
    """Filter leads based on qualification criteria."""
    qualified = [
        lead for lead in leads 
        if lead.is_qualified(min_engagement=settings.scraping.min_engagement_score)
    ]
    print(f"\nFiltered to {len(qualified)} qualified leads (from {len(leads)} total)")
    return qualified


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Multi-Source Lead Scraping Engine - Phase 1"
    )
    parser.add_argument(
        '--sources',
        nargs='+',
        choices=['reddit', 'discord', 'slack'],
        default=['reddit', 'discord', 'slack'],
        help='Sources to scrape (default: all)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/leads.json',
        help='Output file path (default: data/leads.json)'
    )
    parser.add_argument(
        '--no-filter',
        action='store_true',
        help='Skip lead qualification filtering'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Multi-Source Lead Scraping Engine - Phase 1")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Sources: {', '.join(args.sources)}")
    print(f"Keywords: {len(settings.scraping.keywords)}")
    print(f"Output: {args.output}")
    
    # Validate settings
    if not settings.validate():
        print("\nWarning: Some credentials are missing. Scrapers may fail.")
    
    try:
        # Run scrapers
        leads = asyncio.run(run_scrapers(args.sources))
        
        if not leads:
            print("\n✗ No leads found")
            return
        
        # Filter qualified leads
        if not args.no_filter:
            leads = filter_qualified_leads(leads)
        
        # Save results
        print(f"\nSaving leads to {args.output}...")
        append_leads(leads, args.output)
        
        print("\n" + "=" * 60)
        print(f"✓ Successfully scraped {len(leads)} leads")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user")
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        if settings.debug_mode:
            raise


if __name__ == "__main__":
    main()
