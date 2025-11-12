"""LLM-based lead qualification using OpenAI GPT-4-turbo."""

import os
import json
import asyncio
from typing import Optional
from datetime import datetime

from openai import OpenAI
from openai import OpenAIError

from models.lead import Lead


class LLMLeadQualifier:
    """Qualify leads using GPT-4-turbo for intelligent service matching."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4-turbo"):
        """
        Initialize LLM qualifier.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use (default: gpt-4-turbo)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
    
    def _build_qualification_prompt(self, lead: Lead) -> str:
        """Build prompt for lead qualification."""
        # Extract relevant information
        content = lead.content[:2000]  # Limit to 2000 chars to save tokens
        title = lead.title or "No title"
        source = lead.source
        author = lead.author
        engagement = lead.engagement_score
        
        # Build metadata summary
        metadata_summary = ""
        if lead.metadata:
            service_types = lead.metadata.get('service_types', [])
            if service_types:
                metadata_summary = f"\nPre-classified categories: {', '.join(service_types)}"
        
        prompt = f"""You are an expert sales lead qualifier for a technology services company that specializes in:

**OUR SERVICES:**
1. **RWA Tokenization** - Tokenizing real-world assets (real estate, commodities, art) on blockchain
2. **Crypto/Web3 Development** - DeFi platforms, Web3 apps, smart contracts, crypto payment integration
3. **Blockchain Solutions** - Custom blockchain development, distributed ledger systems, consensus protocols
4. **AI/ML Integration** - AI automation, machine learning models, chatbots, neural networks, predictive analytics

**YOUR TASK:** Analyze this lead and determine if they are a POTENTIAL CLIENT actively seeking our services.

**Lead Information:**
- Source: {source}
- Author: {author}
- Title: {title}
- Engagement Score: {engagement}{metadata_summary}

**Content:**
{content}

**QUALIFICATION CRITERIA:**

**HIGH CONFIDENCE (0.8-1.0) - QUALIFIED:**
- Uses explicit help-seeking phrases:
  • "need help with/implementing/building"
  • "looking for consultant/developer/expert"
  • "recommend a solution/platform/service"
  • "struggling with/can't figure out"
  • "seeking expert in/looking to hire"
  • "any suggestions for/best tool for"
- Describes a specific problem they want solved
- Asks direct questions about implementation/solutions
- Expresses urgency or pain points needing resolution

**MODERATE CONFIDENCE (0.5-0.7) - POTENTIALLY QUALIFIED:**
- Discusses challenges but doesn't explicitly ask for help
- Mentions exploring solutions or considering options
- Asks general "how to" questions that could lead to service needs
- Shows interest in learning about implementation approaches

**LOW CONFIDENCE (0.0-0.4) - NOT QUALIFIED:**
- Job postings: "hiring", "looking for full-time", "open position", "career opportunity"
- News/updates: "just launched", "announcing", "proud to share", "check out this article"
- General discussion: "what do you think about", "interesting topic", casual opinions
- Self-promotion: marketing their own products/services
- Educational content: explaining concepts without seeking help

**SERVICE MATCHING:**
- **RWA Tokenization**: mentions tokenizing assets, real estate on blockchain, asset-backed tokens
- **Crypto/Web3**: DeFi, Web3, smart contracts, crypto integration, wallet, blockchain payments
- **Blockchain Solutions**: distributed ledger, consensus, blockchain architecture, custom chains
- **AI/ML**: AI automation, machine learning, chatbots, neural networks, ML models, predictive analytics

**CRITICAL DISTINCTIONS:**
1. **ASKING FOR HELP** (qualified) vs **JUST DISCUSSING** (not qualified)
2. **SERVICE INQUIRY** (qualified) vs **JOB POSTING** (not qualified)
3. **PROBLEM TO SOLVE** (qualified) vs **SHARING KNOWLEDGE** (not qualified)

**Response Format (JSON only, no markdown):**
{{
  "is_qualified": true/false,
  "confidence_score": 0.0-1.0,
  "reason": "Brief explanation referencing specific phrases or patterns found (1-2 sentences)",
  "service_match": ["RWA Tokenization", "Crypto/Web3", "Blockchain Solutions", "AI/ML"] or []
}}"""
        
        return prompt
    
    def qualify_lead(self, lead: Lead) -> dict:
        """
        Qualify a lead using GPT-4-turbo.
        
        Args:
            lead: Lead object to qualify
            
        Returns:
            dict with:
                - is_qualified (bool): Whether lead is qualified
                - confidence_score (float): Confidence 0.0-1.0
                - reason (str): Explanation
                - service_match (list): Matching services
                - error (str, optional): Error message if failed
        """
        try:
            prompt = self._build_qualification_prompt(lead)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a sales lead qualification expert. Always respond with valid JSON only, no markdown formatting."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent results
                max_tokens=300,
                response_format={"type": "json_object"}  # Enforce JSON response
            )
            
            # Parse response
            result_text = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            result = json.loads(result_text)
            
            # Validate result structure
            required_keys = {"is_qualified", "confidence_score", "reason", "service_match"}
            if not required_keys.issubset(result.keys()):
                return {
                    "is_qualified": False,
                    "confidence_score": 0.0,
                    "reason": "Invalid response structure from LLM",
                    "service_match": [],
                    "error": "Missing required keys in LLM response"
                }
            
            # Ensure correct types
            result["is_qualified"] = bool(result["is_qualified"])
            result["confidence_score"] = float(result["confidence_score"])
            result["reason"] = str(result["reason"])
            result["service_match"] = list(result["service_match"]) if result["service_match"] else []
            
            # Clamp confidence score to 0-1
            result["confidence_score"] = max(0.0, min(1.0, result["confidence_score"]))
            
            return result
            
        except OpenAIError as e:
            return {
                "is_qualified": False,
                "confidence_score": 0.0,
                "reason": f"OpenAI API error: {str(e)}",
                "service_match": [],
                "error": str(e)
            }
        
        except json.JSONDecodeError as e:
            return {
                "is_qualified": False,
                "confidence_score": 0.0,
                "reason": f"Failed to parse LLM response as JSON: {str(e)}",
                "service_match": [],
                "error": f"JSON parse error: {str(e)}"
            }
        
        except Exception as e:
            return {
                "is_qualified": False,
                "confidence_score": 0.0,
                "reason": f"Unexpected error: {str(e)}",
                "service_match": [],
                "error": str(e)
            }
    
    def batch_qualify_leads(self, leads: list[Lead], max_leads: Optional[int] = None) -> list[dict]:
        """
        Qualify multiple leads in batch (sequential).
        
        Args:
            leads: List of Lead objects
            max_leads: Maximum number of leads to process (for cost control)
            
        Returns:
            List of qualification results with lead info
        """
        results = []
        process_count = min(len(leads), max_leads) if max_leads else len(leads)
        
        print(f"🤖 Starting LLM qualification for {process_count} leads...")
        
        for idx, lead in enumerate(leads[:process_count], 1):
            print(f"  [{idx}/{process_count}] Qualifying: {lead.author} - {(lead.title or lead.content[:50])[:60]}...")
            
            qualification = self.qualify_lead(lead)
            
            # Add lead reference
            result = {
                "lead_url": lead.url,
                "lead_author": lead.author,
                "lead_source": lead.source,
                **qualification
            }
            
            results.append(result)
            
            # Print result
            status = "✅ QUALIFIED" if qualification["is_qualified"] else "❌ Not qualified"
            confidence = qualification["confidence_score"]
            print(f"     {status} (confidence: {confidence:.2f}) - {qualification['reason'][:80]}")
        
        # Summary
        qualified_count = sum(1 for r in results if r["is_qualified"])
        print(f"\n✅ Qualification complete: {qualified_count}/{process_count} leads qualified")
        
        return results
    
    async def qualify_lead_async(self, lead: Lead, idx: int, total: int) -> dict:
        """
        Qualify a lead asynchronously with progress indicator.
        
        Args:
            lead: Lead object to qualify
            idx: Current lead index (1-based)
            total: Total number of leads
            
        Returns:
            dict with qualification results and lead info
        """
        print(f"  Qualifying lead {idx}/{total}...")
        
        # Run synchronous qualify_lead in thread pool
        qualification = await asyncio.to_thread(self.qualify_lead, lead)
        
        # Add lead reference
        result = {
            "lead_url": lead.url,
            "lead_author": lead.author,
            "lead_source": lead.source,
            **qualification
        }
        
        return result
    
    async def qualify_leads_concurrent(
        self, 
        leads: list[Lead], 
        max_concurrent: int = 5,
        max_leads: Optional[int] = None
    ) -> list[dict]:
        """
        Qualify multiple leads concurrently with rate limiting.
        
        Args:
            leads: List of Lead objects
            max_concurrent: Maximum concurrent API requests
            max_leads: Maximum total leads to process (for cost control)
            
        Returns:
            List of qualification results in same order as input leads
        """
        process_count = min(len(leads), max_leads) if max_leads else len(leads)
        leads_to_process = leads[:process_count]
        
        print(f"🤖 Starting concurrent LLM qualification for {process_count} leads...")
        print(f"   Max concurrent requests: {max_concurrent}")
        
        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def qualify_with_semaphore(lead: Lead, idx: int) -> dict:
            async with semaphore:
                return await self.qualify_lead_async(lead, idx, process_count)
        
        # Create tasks for all leads
        tasks = [
            qualify_with_semaphore(lead, idx)
            for idx, lead in enumerate(leads_to_process, 1)
        ]
        
        # Run all tasks concurrently (but limited by semaphore)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        final_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                # Create error result for failed leads
                lead = leads_to_process[idx]
                final_results.append({
                    "lead_url": lead.url,
                    "lead_author": lead.author,
                    "lead_source": lead.source,
                    "is_qualified": False,
                    "confidence_score": 0.0,
                    "reason": f"Processing error: {str(result)}",
                    "service_match": [],
                    "error": str(result)
                })
            else:
                final_results.append(result)
        
        # Summary
        qualified_count = sum(1 for r in final_results if r.get("is_qualified", False))
        print(f"\n✅ Qualification complete: {qualified_count}/{process_count} leads qualified")
        
        return final_results


# Convenience function for single lead qualification
def qualify_lead(lead: Lead) -> dict:
    """
    Qualify a single lead using GPT-4-turbo.
    
    Args:
        lead: Lead object to qualify
        
    Returns:
        dict with qualification results
    """
    qualifier = LLMLeadQualifier()
    return qualifier.qualify_lead(lead)


def qualify_leads_batch(leads: list[Lead], max_leads: Optional[int] = None) -> list[dict]:
    """
    Qualify multiple leads in batch (sequential).
    
    Args:
        leads: List of Lead objects
        max_leads: Maximum number to process
        
    Returns:
        List of qualification results
    """
    qualifier = LLMLeadQualifier()
    return qualifier.batch_qualify_leads(leads, max_leads)


async def qualify_leads_concurrent(
    leads: list[Lead], 
    max_concurrent: int = 5,
    max_leads: Optional[int] = None
) -> list[dict]:
    """
    Qualify multiple leads concurrently using asyncio.
    
    Args:
        leads: List of Lead objects
        max_concurrent: Maximum concurrent API requests (default: 5)
        max_leads: Maximum total leads to process (for cost control)
        
    Returns:
        List of qualification results in same order as input leads
        
    Example:
        results = await qualify_leads_concurrent(leads, max_concurrent=5, max_leads=20)
    """
    qualifier = LLMLeadQualifier()
    return await qualifier.qualify_leads_concurrent(leads, max_concurrent, max_leads)
