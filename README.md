# Multi-Source Lead Scraping Engine

AI-powered lead scraper that collects and qualifies leads from Reddit, Discord, Slack, and LinkedIn using advanced LLM qualification with Gemini 2.5 Flash fallback.

**Phase 1 (Section 1.1)** - Multi-platform scraping with keyword filtering, rate limiting, and intelligent lead qualification.

## Features

✅ **Multi-Source Scraping**: Reddit, Discord, Slack, LinkedIn (public & Apify)  
✅ **Smart Pre-Validation**: 94.6% cost savings - filters spam before LLM calls  
✅ **Dual LLM System**: OpenAI GPT-4-turbo (primary) + Gemini 2.5 Flash (fallback)  
✅ **Bulletproof Reliability**: Automatic Gemini fallback when OpenAI quota exceeded  
✅ **Advanced Filtering**: 3-stage pre-validation (spam, help phrases, implicit signals)  
✅ **Rate Limiting**: Respects platform limits (60/min Reddit, 50/sec Discord, 1/sec Slack)  
✅ **Lead Qualification**: AI-powered detection of genuine service inquiries  
✅ **Auto-Deduplication**: By URL with intelligent merging  
✅ **Excel Export**: Qualified leads with confidence scores  
✅ **CLI Interface**: Flexible source and service selection  

## Requirements

- Python 3.12.10
- API credentials for Reddit, Discord, Slack, and/or LinkedIn
- OpenAI API key (primary LLM)
- Gemini API key (fallback LLM - optional but recommended)

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

#### OpenAI API Setup
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key (starts with `sk-proj-...`)
4. Note: GPT-4-turbo costs ~$0.01 per lead

#### Gemini API Setup (Fallback - Recommended)
1. Go to https://makersuite.google.com/app/apikey
2. Create a new API key
3. Copy the key (starts with `AIza...`)
4. Gemini 2.5 Flash is 10x cheaper and faster than GPT-4
5. Automatically activates when OpenAI quota exceeded

#### LinkedIn Scraping Setup
**Option 1: Public Scraping (Experimental)**
- Set `LINKEDIN_PUBLIC_ENABLED=true` in .env
- ⚠️ High ban risk - use with caution

**Option 2: Apify Integration (Recommended)**
1. Go to https://console.apify.com/account/integrations
2. Get free API token ($5 credit = ~5000 posts)
3. Set `LINKEDIN_APIFY_ENABLED=true` in .env
4. Copy token to `APIFY_TOKEN` in .env

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


## Quick Start

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure credentials
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac
# Edit .env with your API keys

# 4. Run scraper with qualification
python main.py --sources reddit --service rwa --qualify --max-total-leads 500
```

## Usage Examples

```bash
# Scrape Reddit for RWA inquiries with LLM qualification
python main.py --sources reddit --service rwa_reddit --qualify

# Scrape LinkedIn via Apify for crypto leads
python main.py --sources linkedin_apify --service crypto_linkedin --qualify

# Scrape multiple sources for blockchain leads
python main.py --sources reddit linkedin_apify --service blockchain --qualify

# Limit to 500 leads and export to custom file
python main.py --sources reddit --service rwa --qualify --max-total-leads 500 --output my_leads.json

# Filter for specific service during qualification
python main.py --sources reddit --qualify --filter-service RWA

# Skip LLM qualification (just scrape)
python main.py --sources reddit --service rwa_reddit --no-filter
```

## Available Services

- **Platform-specific**: `rwa_reddit`, `rwa_linkedin`, `crypto_reddit`, `crypto_linkedin`, `ai_reddit`, `ai_linkedin`, `blockchain_reddit`, `blockchain_linkedin`
- **Universal**: `rwa`, `crypto`, `ai`, `blockchain`, `general`, `all`

## LLM Qualification System

### Dual-Tier Architecture
1. **Primary LLM**: OpenAI GPT-4-turbo
   - High quality, strict filtering
   - ~$0.01 per lead
   - Handles initial qualification attempts

2. **Fallback LLM**: Gemini 2.5 Flash
   - Activates when OpenAI fails (quota/rate limits)
   - 10x cheaper (~$0.001 per lead)
   - Faster response time (1-2s vs 2-3s)
   - Ensures zero downtime

### Pre-Validation Filter (94.6% Cost Savings)
Before expensive LLM calls, leads go through 3-stage validation:

1. **Stage 1**: Spam/Promotion Detection
   - Filters obvious spam, self-promotion, hiring posts
   - Checks for 2+ spam indicators

2. **Stage 2**: Help-Seeking Phrases
   - Detects 30+ explicit inquiry patterns
   - Examples: "looking for", "need help", "recommend", "anyone know"

3. **Stage 3**: Implicit Inquiry Signals
   - Identifies subtle service inquiries
   - Requires 2+ signals: budget mentions, struggling, time pressure, etc.

**Result**: Only 5.4% of leads reach LLM (saves $143 per 15k leads)

### Qualification Response
Each lead receives:
```json
{
  "is_qualified": true,
  "confidence_score": 0.85,
  "reason": "User explicitly asks for RWA tokenization platform...",
  "service_match": ["RWA", "Blockchain", "Crypto"],
  "llm_provider": "gemini"  // or "openai"
}
```

## Project Structure

```
ai-sales-agent/
├── config/                      # Configuration and settings
│   ├── settings.py             # Keyword lists, subreddits, rate limits
│   └── __init__.py
├── models/                      # Data models
│   ├── lead.py                 # Lead class with qualification support
│   └── __init__.py
├── scrapers/                    # Platform-specific scrapers
│   ├── base.py                 # Base scraper abstract class
│   ├── reddit_scraper.py       # Reddit (PRAW)
│   ├── discord_scraper.py      # Discord bot integration
│   ├── slack_scraper.py        # Slack bot integration
│   ├── linkedin_public_scraper.py  # Public LinkedIn (high risk)
│   ├── linkedin_apify_scraper.py   # LinkedIn via Apify (recommended)
│   └── __init__.py
├── storage/                     # Data persistence
│   ├── json_handler.py         # JSON storage with deduplication
│   ├── excel_handler.py        # Excel export for qualified leads
│   └── __init__.py
├── utils/                       # Utilities
│   ├── llm_handler.py          # OpenAI + Gemini qualification
│   ├── rate_limiter.py         # Rate limiting for API calls
│   ├── linkedin_helpers.py     # LinkedIn-specific utilities
│   └── __init__.py
├── data/                        # Output directory
│   ├── leads.json              # All leads with deduplication
│   └── qualified_leads_*.xlsx  # Excel exports
├── .env                         # Environment variables (not in git)
├── .env.example                # Template for credentials
├── main.py                      # CLI entry point
├── requirements.txt             # Python dependencies
├── GEMINI_FALLBACK_COMPLETE.md # Gemini implementation docs
├── PREVALIDATION_EXPLAINED.md  # Pre-validation filter docs
└── README.md                    # This file
```

## Configuration

### Environment Variables (.env)
```bash
# Reddit API
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=LeadScrapingBot/1.0

# Discord Bot
DISCORD_BOT_TOKEN=your_discord_token

# Slack API
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_APP_TOKEN=xapp-your-slack-app-token

# LinkedIn (Apify - Recommended)
LINKEDIN_APIFY_ENABLED=true
APIFY_TOKEN=apify_api_your_token
LINKEDIN_APIFY_ACTOR=supreme_coder/linkedin-post

# LinkedIn (Public - Experimental)
LINKEDIN_PUBLIC_ENABLED=false
LINKEDIN_COOKIE=your_li_at_cookie

# OpenAI (Primary LLM)
OPENAI_API_KEY=sk-proj-your_openai_key
LLM_MODEL=gpt-4-turbo
MIN_CONFIDENCE_SCORE=0.7
MAX_CONCURRENT_LLM_REQUESTS=5

# Gemini (Fallback LLM)
GEMINI_API_KEY=AIza_your_gemini_key
```

### Settings (config/settings.py)
Customize:
- Keywords for filtering (30+ help-seeking phrases)
- Subreddits to monitor (RWA, crypto, blockchain, AI/ML)
- Rate limits per platform
- Engagement thresholds
- Pre-validation parameters

## Output Files

### JSON Storage (data/leads.json)
- All scraped leads with deduplication by URL
- Includes qualification results (`qualification_result` field)
- Preserves history across multiple runs
- Auto-merges duplicate leads

### Excel Export (data/qualified_leads_*.xlsx)
- Only qualified leads (is_qualified=true)
- Sorted by confidence score (highest first)
- Columns: Title, Content, Author, URL, Source, Confidence, Reason, Services, LLM Provider
- Generated automatically after each qualification run

## Performance Metrics

### Cost Savings
- **Pre-validation filter**: Blocks 94.6% of leads before LLM
- **Example**: 15,161 leads → Only 821 reach LLM
- **Cost savings**: ~$143 per 15k leads (at $0.01/lead)
- **Gemini fallback**: Additional 10x savings when activated

### Speed
- **OpenAI GPT-4-turbo**: 2-3 seconds per lead
- **Gemini 2.5 Flash**: 1-2 seconds per lead
- **Pre-validation**: <0.1 seconds per lead

### Reliability
- **Zero downtime**: Gemini catches all OpenAI failures
- **Quota protection**: Automatic fallback on 429 errors
- **Rate limit handling**: Respects all platform limits

## Troubleshooting

### OpenAI Quota Exceeded
✅ **Gemini automatically activates** - no action needed!
- You'll see: `⚠️ OpenAI failed..., trying Gemini fallback...`
- Leads continue processing seamlessly

### No Qualified Leads
- Check `MIN_CONFIDENCE_SCORE` in .env (default: 0.7)
- Review pre-validation logic in `PREVALIDATION_EXPLAINED.md`
- Most leads are discussions, not inquiries (strict filtering by design)

### LinkedIn Ban Risk
- Use Apify integration instead of public scraping
- Set `LINKEDIN_PUBLIC_ENABLED=false`
- Apify provides $5 free credit (~5000 posts)

### Rate Limiting
- Default limits: 60/min (Reddit), 50/sec (Discord), 1/sec (Slack)
- Adjust `MAX_CONCURRENT_LLM_REQUESTS` if hitting OpenAI rate limits
- Gemini has more generous quota than OpenAI

## Documentation

- **GEMINI_FALLBACK_COMPLETE.md** - Dual LLM system architecture and implementation
- **PREVALIDATION_EXPLAINED.md** - 3-stage pre-validation filter explained with examples
- **config/settings.py** - All keywords, subreddits, and configuration parameters

## Example Run

```bash
$ python main.py --sources reddit --service rwa_reddit --qualify --max-total-leads 500

✅ Gemini 2.5 Flash fallback configured successfully
🔍 Scraping from: reddit
   Service: rwa_reddit
   Max leads: 500

🤖 Starting LLM qualification for 821 leads...
  Qualifying lead 1/821...
  Qualifying lead 2/821...
  ⚠️ OpenAI failed (Error code: 429...), trying Gemini fallback...  ← Automatic!
  Qualifying lead 3/821...
  ...

✅ Qualification complete: 12/821 leads qualified
   💰 API savings: 14,340/15,161 leads filtered by pre-validation

📊 Exporting qualified leads to data/qualified_leads_20251115_125601.xlsx...
✅ Exported 12 leads sorted by confidence score

✓ Successfully scraped 15,085 leads
```

## Contributing

This is a proprietary project. For questions or issues, contact the development team.

## License

Proprietary - All rights reserved
