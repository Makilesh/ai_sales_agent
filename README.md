# Multi-Source Lead Scraping Engine

AI-powered lead scraper that collects and qualifies leads from Reddit, Discord, and Slack.

**Phase 1 (Section 1.1)** - Multi-platform scraping with keyword filtering, rate limiting, and lead qualification.

## Features

✅ Concurrent scraping from Reddit, Discord, Slack  
✅ Keyword-based filtering  
✅ Rate limiting (60/min Reddit, 50/sec Discord, 1/sec Slack)  
✅ Lead qualification and deduplication  
✅ JSON storage with auto-deduplication  
✅ CLI interface with source selection  

## Requirements

- Python 3.12.10
- API credentials for Reddit, Discord, and/or Slack

## Quick Start

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure credentials
copy .env.example .env
# Edit .env with your API keys

#### Reddit API Setup
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Choose "script" as the app type
4. Copy the client ID and client secret

#### Discord Bot Setup
1. Go to https://discord.com/developers/applications
2. Create a "New Application"
3. Go to the "Bot" section and create a bot
4. Copy the bot token

#### Slack API Setup
1. Go to https://api.slack.com/apps
2. Create a "New App"
3. Install the app to your workspace
4. Copy the Bot User OAuth Token and App-Level Token

## Project Structure

```
ai-sales-agent/
├── .env                    # Environment variables (not in git)
├── .env.example           # Template for environment variables
├── .gitignore             # Git ignore rules
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Next Steps

After setup, you can begin implementing:
- Reddit scraper module
- Discord scraper module
- Slack scraper module
- Data processing pipeline
- Lead qualification logic

## License

Proprietary - All rights reserved


# Scrape all sources
python main.py

# Scrape specific sources
python main.py --sources reddit
python main.py --sources reddit discord

# Custom output file
python main.py --output data/leads_2025.json

# Skip qualification filtering
python main.py --no-filter
```

## Project Structure

```
ai-sales-agent/
├── config/              # Configuration and settings
├── models/              # Lead data model
├── scrapers/            # Platform-specific scrapers
│   ├── base.py         # Base scraper class
│   ├── reddit_scraper.py
│   ├── discord_scraper.py
│   └── slack_scraper.py
├── storage/             # JSON storage handler
├── utils/               # Rate limiter utilities
├── main.py             # CLI entry point
└── requirements.txt    # Dependencies
```

## Configuration

Edit `config/settings.py` to customize:
- Keywords for filtering
- Subreddits to monitor
- Channel IDs (Discord/Slack)
- Rate limits
- Engagement thresholds

## Notes

- Leads are deduplicated by URL
- Results saved to `data/leads.json` by default
- Rate limiting respects platform limits
- Empty credentials skip that platform gracefully

For detailed review and advanced features, see `REVIEW.md`.