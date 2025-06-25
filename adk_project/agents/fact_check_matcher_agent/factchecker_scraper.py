import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import List, Dict
import hashlib
import time
import os
from fuzzywuzzy import fuzz
import urllib.parse
from urllib.parse import urlparse
from adk_project.utils.firecrawl import firecrawl_search_tool, firecrawl_crawl_and_match

FACTCHECKERS = [
    "https://www.factcheck.org/",
    "https://reporterslab.org/fact-checking/",
    "https://apnews.com/ap-fact-check",
    "https://www.snopes.com/",
    "https://www.politifact.com/",
    "https://fullfact.org/",
    "https://factuel.afp.com/",
    "https://www.reuters.com/fact-check",  # Reuters Fact Check añadido
    "https://www.washingtonpost.com/politics/fact-checker/",  # Washington Post Fact Checker añadido
    "https://factcheckni.org/",
    "https://factcheck.kz/",
    "https://www.factcrescendo.com/",
    "https://www.bbc.com/news/bbcverify"  # BBC Verify añadido
]

CACHE: Dict[str, Dict] = {}
CACHE_TTL = 3600  # 1 hora

def cache_key(query: str) -> str:
    return hashlib.sha256(query.encode()).hexdigest()

async def get_factchecker_claims(main_claim: str) -> List[Dict]:
    print(f"[get_factchecker_claims] Searching claim: {main_claim}")
    key = cache_key(main_claim)
    now = time.time()
    if key in CACHE and now - CACHE[key]["ts"] < CACHE_TTL:
        print("[get_factchecker_claims] Using cache")
        return CACHE[key]["data"]
    
    domains = [urlparse(fc).netloc for fc in FACTCHECKERS]
    claims = []
    
    # Step 1: Enhanced webcrawling with semantic analysis
    print("[get_factchecker_claims] Step 1: Enhanced webcrawling with semantic matching...")
    
    # Extract key terms and concepts from main claim for flexible matching
    key_terms = await extract_key_terms(main_claim)
    
    # Search each fact-checker domain for semantic matches
    for domain in domains:
        print(f"[get_factchecker_claims] Crawling {domain}...")
        domain_claims = await crawl_domain_with_semantic_matching(domain, main_claim, key_terms)
        claims.extend(domain_claims)
    
    # Step 2: Apply semantic similarity analysis using Gemini
    if claims:
        print("[get_factchecker_claims] Step 2: Applying semantic similarity analysis...")
        claims = await enhance_claims_with_semantic_analysis(main_claim, claims)
    
    # Step 3: Sort by relevance and limit results
    claims = sorted(claims, key=lambda x: x.get('semantic_score', 0), reverse=True)[:10]
    
    print(f"[get_factchecker_claims] Final claims found:")
    for claim in claims:
        print(f"  - url: {claim['url']} | semantic_score: {claim.get('semantic_score', 0)} | headline: {claim.get('headline', '')[:60]}...")
    
    CACHE[key] = {"data": claims, "ts": now}
    return claims

async def extract_key_terms(claim: str) -> List[str]:
    """Extract key terms and concepts from claim for flexible matching"""
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        prompt = f"""
        Extract key terms and concepts from this claim for fact-checking search.
        
        Claim: "{claim}"
        
        Return 5-8 key terms that would help find related fact-checks, including:
        - Main subject/topic
        - Key actors/entities
        - Specific claims/numbers
        - Related concepts
        
        Format as comma-separated list, no explanations.
        """
        
        response = model.generate_content(prompt)
        terms = [term.strip() for term in response.text.strip().split(',')]
        return terms[:8]  # Limit to 8 terms
        
    except Exception as e:
        print(f"Error extracting key terms: {e}")
        # Fallback: simple word extraction
        import re
        words = re.findall(r'\b\w{4,}\b', claim.lower())
        return list(set(words))[:8]

async def crawl_domain_with_semantic_matching(domain: str, main_claim: str, key_terms: List[str]) -> List[Dict]:
    """Crawl a fact-checker domain looking for semantic matches"""
    try:
        # Use Firecrawl to search the domain
        search_queries = [
            main_claim,  # Direct claim search
            ' '.join(key_terms[:3]),  # Key terms search
            f'"{key_terms[0]}" fact check' if key_terms else main_claim  # Focused search
        ]
        
        domain_claims = []
        
        for query in search_queries:
            try:
                # Search within specific domain
                from adk_project.utils.firecrawl import firecrawl_scrape_tool
                import aiohttp
                
                # Use Firecrawl search API targeting specific domain
                api_key = os.environ.get("FIRECRAWL_API_KEY")
                if not api_key:
                    continue
                
                url = "https://api.firecrawl.dev/v1/search"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "query": f'"{query}" site:{domain}',
                    "limit": 3,
                    "lang": "en"
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=data, timeout=15) as resp:
                        if resp.status == 200:
                            results = await resp.json()
                            
                            if results and results.get('data'):
                                for result in results['data']:
                                    domain_claims.append({
                                        'url': result.get('url', ''),
                                        'headline': result.get('title', ''),
                                        'main_claim': result.get('description', '')[:300],
                                        'source': domain,
                                        'search_query': query,
                                        'raw_score': 0  # Will be calculated later
                                    })
                        
            except Exception as e:
                print(f"Error searching {domain} with query '{query}': {e}")
                continue
        
        return domain_claims
        
    except Exception as e:
        print(f"Error crawling domain {domain}: {e}")
        return []

async def enhance_claims_with_semantic_analysis(main_claim: str, claims: List[Dict]) -> List[Dict]:
    """Use Gemini to analyze semantic similarity between main claim and found claims"""
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        enhanced_claims = []
        
        for claim in claims:
            try:
                claim_text = claim.get('headline', '') + ' ' + claim.get('main_claim', '')
                
                prompt = f"""
                Analyze the semantic similarity between these two claims for fact-checking purposes.
                
                ORIGINAL CLAIM: "{main_claim}"
                FACT-CHECK CLAIM: "{claim_text}"
                
                Consider:
                - Same topic/subject matter
                - Similar factual assertions
                - Related but different perspectives
                - Contradictory claims on same topic
                
                Return ONLY a JSON object:
                {{
                    "semantic_score": <number 0-100>,
                    "relation_type": "identical|similar|related|contradictory|unrelated",
                    "relevance_reason": "brief explanation"
                }}
                """
                
                response = model.generate_content(prompt)
                result_text = response.text.strip()
                
                # Clean up the response to ensure valid JSON
                if result_text.startswith('```json'):
                    result_text = result_text.replace('```json', '').replace('```', '').strip()
                elif result_text.startswith('```'):
                    result_text = result_text.replace('```', '').strip()
                
                import json
                analysis = json.loads(result_text)
                
                # Add semantic analysis to claim
                enhanced_claim = {
                    **claim,
                    'semantic_score': analysis.get('semantic_score', 0),
                    'relation_type': analysis.get('relation_type', 'unrelated'),
                    'relevance_reason': analysis.get('relevance_reason', ''),
                    'confidence': 'alto' if analysis.get('semantic_score', 0) > 70 else 'medio' if analysis.get('semantic_score', 0) > 40 else 'bajo'
                }
                
                # Only include if semantic score is above threshold
                if analysis.get('semantic_score', 0) > 30:
                    enhanced_claims.append(enhanced_claim)
                    
            except Exception as e:
                print(f"Error analyzing claim semantic similarity: {e}")
                # Include with basic scoring as fallback
                enhanced_claims.append({
                    **claim,
                    'semantic_score': claim.get('raw_score', 0),
                    'relation_type': 'unknown',
                    'confidence': 'bajo'
                })
        
        return enhanced_claims
        
    except Exception as e:
        print(f"Error in semantic analysis: {e}")
        return claims

# Ejemplo de uso:
# claims = asyncio.run(get_factchecker_claims("Coffee prevents cancer"))
# print(claims)
