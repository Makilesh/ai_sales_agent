"""
Analyze scraped leads - show service classification and job posting detection.
Run this to see what types of leads you're getting.
"""

import json
from collections import Counter

# Load leads
with open('data/leads.json', 'r', encoding='utf-8') as f:
    leads = json.load(f)

# Service categories (same as in linkedin_apify_scraper.py)
SERVICE_CATEGORIES = {
    'RWA': [
        'real world asset', 'rwa', 'tokenization', 'tokenize', 
        'asset tokenization', 'real estate token', 'physical asset',
        'commodities', 'tokenized asset', 'on-chain asset'
    ],
    'Crypto': [
        'cryptocurrency', 'crypto', 'bitcoin', 'ethereum', 'defi',
        'decentralized finance', 'crypto exchange', 'crypto wallet',
        'crypto payment', 'crypto integration', 'web3', 'dapp'
    ],
    'Blockchain': [
        'blockchain', 'smart contract', 'distributed ledger', 'dlt',
        'blockchain development', 'blockchain solution', 'blockchain platform',
        'consensus', 'node', 'blockchain integration'
    ],
    'NFT': [
        'nft', 'non-fungible token', 'nft marketplace', 'nft collection',
        'digital collectible', 'nft platform', 'nft minting'
    ],
    'AI/ML': [
        'artificial intelligence', 'machine learning', 'ai solution',
        'ml model', 'deep learning', 'neural network', 'ai integration',
        'chatbot', 'ai automation', 'predictive analytics'
    ],
    'Fintech': [
        'fintech', 'financial technology', 'payment gateway', 'payment processing',
        'digital payment', 'banking solution', 'financial platform',
        'lending platform', 'investment platform'
    ],
    'Development': [
        'software development', 'app development', 'web development',
        'mobile app', 'custom solution', 'api integration',
        'system integration', 'platform development'
    ]
}

# Job posting keywords (expanded)
JOB_KEYWORDS = [
    'hiring', 'looking for a', 'looking for an', 'apply', 'cv', 'resume',
    'join our team', 'years experience', 'open to work', 'candidate',
    'recruitment', 'full-time', 'part-time', 'salary', 'compensation'
]

def classify_service(text):
    """Classify lead by service type."""
    text_lower = text.lower()
    categories = []
    
    for category, keywords in SERVICE_CATEGORIES.items():
        if any(kw.lower() in text_lower for kw in keywords):
            categories.append(category)
    
    return categories if categories else ['General']

def is_job_posting(text):
    """Check if lead is a job posting."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in JOB_KEYWORDS)

# Analyze leads
print("=" * 80)
print("LEAD ANALYSIS REPORT")
print("=" * 80)

# Overall stats
total_leads = len(leads)
linkedin_leads = [l for l in leads if l['source'] == 'linkedin']
reddit_leads = [l for l in leads if l['source'] == 'reddit']

print(f"\n📊 OVERALL STATS:")
print(f"  • Total Leads: {total_leads}")
print(f"  • LinkedIn: {len(linkedin_leads)}")
print(f"  • Reddit: {len(reddit_leads)}")

# Job posting analysis
job_postings = [l for l in linkedin_leads if is_job_posting(l['content'])]
service_leads = [l for l in linkedin_leads if not is_job_posting(l['content'])]

print(f"\n🎯 JOB POSTING FILTER ANALYSIS (LinkedIn only):")
print(f"  • Total LinkedIn Leads: {len(linkedin_leads)}")
print(f"  • Likely Job Postings: {len(job_postings)} ({len(job_postings)/len(linkedin_leads)*100:.1f}%)")
print(f"  • Potential Service Inquiries: {len(service_leads)} ({len(service_leads)/len(linkedin_leads)*100:.1f}%)")

# Service classification
print(f"\n🏷️  SERVICE TYPE CLASSIFICATION:")
service_counter = Counter()
for lead in service_leads:
    categories = classify_service(lead['content'] + " " + (lead.get('title') or ''))
    for cat in categories:
        service_counter[cat] += 1

for service_type, count in service_counter.most_common():
    print(f"  • {service_type}: {count} leads")

# Sample good leads
print(f"\n✅ SAMPLE SERVICE INQUIRY LEADS (Non-Job Postings):")
for i, lead in enumerate(service_leads[:5], 1):
    categories = classify_service(lead['content'] + " " + (lead.get('title') or ''))
    service_tag = ", ".join(categories)
    title = lead.get('title', 'No title')[:60]
    print(f"\n  {i}. [{service_tag}] {title}...")
    print(f"     Author: {lead['author']}")
    print(f"     Preview: {lead['content'][:100]}...")

# Sample job postings
print(f"\n❌ SAMPLE JOB POSTINGS (Should be filtered out):")
for i, lead in enumerate(job_postings[:5], 1):
    title = lead.get('title', 'No title')[:60]
    print(f"\n  {i}. {title}...")
    print(f"     Author: {lead['author']}")
    print(f"     Preview: {lead['content'][:100]}...")

print("\n" + "=" * 80)
print(f"💡 RECOMMENDATION: {len(job_postings)} leads need to be filtered out")
print("=" * 80)
