from google.adk.agents import LlmAgent
from adk_project.agents.response_formatter_agent.prompt import FORMATTER_PROMPT
import asyncio
import os
from adk_project.utils.firecrawl import firecrawl_search_tool
import google.generativeai as genai
import requests

AGUI_RESPONSE_SCHEMA = {
    "headline": "str",
    "url": "str",
    "score": "int (0-3)",
    "score_label": "str (e.g. 'False', 'True', 'Misleading', 'Context Needed')",
    "main_claim": "str",
    "detailed_analysis": "str",
    "verified_sources": "list[str]",
    "recommendation": "str",
    "media_literacy_tip": "str",
    "processing_time": "float",
    "confidence_level": "int",
    "sources_checked": "int",
    "original_source_label": "str",
    "original_source_url": "str",
    "verified_sources_label": "str"
}

class ResponseFormatterAgent(LlmAgent):
    def __init__(self):
        super().__init__(
            name="ResponseFormatterAgent",
            instruction=FORMATTER_PROMPT + "\n\nLa respuesta debe ser un JSON con la siguiente estructura: " + str(AGUI_RESPONSE_SCHEMA) + "\n\nToma los datos de 'scored_result', 'validated_article', 'match_results' y empaquétalos en 'agui_response' para el frontend.",
            description="Formatea el resultado para AG-UI y frontend custom.",
            output_key="agui_response",
            model="gemini-2.5-flash"
        )

    async def run_async(self, ctx):
        # Empaqueta explícitamente los resultados previos en 'agui_response'
        state = ctx.session.state
        scored = state.get('scored_result', {})
        article = state.get('validated_article', {})
        matches = state.get('match_results', {}).get('matches', [])
        agui_response = {
            "headline": article.get("headline", ""),
            "url": article.get("url", ""),
            "score": scored.get("score", None),
            "score_label": scored.get("label", ""),
            "main_claim": scored.get("main_claim", ""),
            "detailed_analysis": scored.get("detailed_analysis", ""),
            "verified_sources": scored.get("verified_sources", []),
            "recommendation": scored.get("recommendation", ""),
            "media_literacy_tip": scored.get("media_literacy_tip", ""),
            "processing_time": scored.get("processing_time", 0.0),
            "confidence_level": scored.get("confidence_level", 0),
            "sources_checked": len(matches),
            "original_source_label": "Medium Risk",  # Always in English
            "original_source_url": article.get("url", ""),
            "verified_sources_label": "High Trust"  # Always in English
        }
        # 1. Recommendation y media_literacy_tip más contextuales
        if matches:
            recommendation = "Based on related fact-checks, review the following sources for verification and context."
            media_literacy_tip = "Compare the main claim with the headlines and conclusions of the fact-checkers listed."
        else:
            recommendation = "No direct fact-checks found, but similar topics were identified. Review the closest matches and consider the credibility of the sources."
            media_literacy_tip = "If no direct match is found, look for similar claims in reputable fact-checking sites and cross-reference information."
        agui_response["recommendation"] = recommendation
        agui_response["media_literacy_tip"] = media_literacy_tip
        # 2. detailed_analysis con Gemini
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        if matches:
            context_text = "\n".join([f"Headline: {c['headline']}\nClaim: {c['main_claim']}" for c in matches[:3]])
            prompt = f"Analyze the following fact-checks and briefly assess the plausibility of the main claim based on these sources.\nClaim: {scored.get('main_claim', '')}\nFact-checks:\n{context_text}"
            detailed_analysis = model.generate_content(prompt).text
        else:
            # 3. Si no hay fact-checkers directos, buscar en otros sitios verificados
            fallback_domains = [
                "snopes.com", "fullfact.org", "factcheck.org", "reuters.com", "politifact.com", "bbc.com", "washingtonpost.com"
            ]
            firecrawl_results = await firecrawl_search_tool(scored.get('main_claim', ''), fallback_domains, limit=5, include_subdomains=True, similarity_threshold=60)
            context_text = "\n".join([f"Headline: {r.get('title', '')}\nClaim: {r.get('markdown', '')[:200]}" for r in firecrawl_results.get('results', [])])
            prompt = f"Given the following related fact-checks from reputable sources, briefly assess the plausibility of the main claim.\nClaim: {scored.get('main_claim', '')}\nFact-checks:\n{context_text}"
            detailed_analysis = model.generate_content(prompt).text
        agui_response["detailed_analysis"] = detailed_analysis
        state["agui_response"] = agui_response
        yield  # Para cumplir con la interfaz async

    def generate_agui_response(claim, claims_found, original_url, factchecker_domains, fallback_domains=None):
        # Inicializar modelo Gemini
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        perplexity_used = False
        # 1. Priorizar fact-checkers: si hay claims_found de la lista prioritaria, usarlos primero
        if claims_found:
            recommendation = "Based on related fact-checks from trusted fact-checkers, review the following sources for verification and context."
            media_literacy_tip = "Compare the main claim with the headlines and conclusions of the prioritized fact-checkers listed."
            context_text = "\n".join([f"Headline: {c['headline']}\nClaim: {c['main_claim']}" for c in claims_found[:3]])
            prompt = f"Analyze the following fact-checks from trusted fact-checkers and briefly assess the plausibility of the main claim based on these sources.\nClaim: {claim}\nFact-checks:\n{context_text}"
            detailed_analysis = model.generate_content(prompt).text
        else:
            # 2. Si no hay matches suficientemente relacionados en fact-checkers, usar medios alternativos verificados
            recommendation = "No direct fact-checks found in main fact-checkers, but similar topics were identified in other reputable sources. Review the closest matches and consider the credibility of the sources."
            media_literacy_tip = "If no direct match is found in main fact-checkers, look for similar claims in reputable fact-checking sites and cross-reference information."
            fallback_domains = fallback_domains or [
                "snopes.com", "fullfact.org", "factcheck.org", "reuters.com", "politifact.com", "bbc.com", "washingtonpost.com"
            ]
            firecrawl_results = asyncio.run(firecrawl_search_tool(claim, fallback_domains, limit=5, include_subdomains=True, similarity_threshold=60))
            context_text = "\n".join([f"Headline: {r.get('title', '')}\nClaim: {r.get('markdown', '')[:200]}" for r in firecrawl_results.get('results', [])])
            if not firecrawl_results.get('results'):
                perplexity_api_key = os.environ.get("PERPLEXITY_API_KEY")
                sonar_content = perplexity_sonar_search(claim, perplexity_api_key, domains=fallback_domains)
                context_text = sonar_content
                perplexity_used = True
            prompt = f"Based on the following information from official news channels and fact-checkers, briefly assess the plausibility of the main claim.\nClaim: {claim}\nFact-checks:\n{context_text}"
            detailed_analysis = model.generate_content(prompt).text
        # 1. Main claim: resumido y limpio
        def clean_main_claim(text):
            import re
            # Elimina links, markdown y deja solo una frase breve
            text = re.sub(r'\[.*?\]\(.*?\)', '', text)  # elimina markdown links
            text = re.sub(r'[^\w\s.,\'-]', '', text)  # elimina caracteres raros
            text = text.strip()
            # Limita a 200 caracteres o primer punto
            if '.' in text:
                text = text.split('.')[0] + '.'
            return text[:200]
        # 2. detailed_analysis: solo un párrafo breve sobre verosimilitud
        def brief_analysis(text):
            # Limita a 2-3 frases, elimina listas y explicaciones largas
            import re
            text = re.sub(r'\*\*.*?\*\*', '', text)  # elimina markdown bold
            text = re.sub(r'\n+', ' ', text)
            text = text.strip()
            sentences = text.split('.')
            return '. '.join(sentences[:2]).strip() + '.'
        # 3. recommendation: juicio de calidad del medio
        def media_quality_recommendation(source_label):
            if source_label == 'High Trust':
                return "This news comes from a highly reputable source."
            elif source_label == 'Medium Risk':
                return "This news comes from a generally reliable source, but cross-check with other outlets is advised."
            else:
                return "Source credibility is unclear. Seek confirmation from trusted media."
        # 4. media_literacy_tip: sugerir atención a datos concretos
        def factual_tip():
            return "Pay attention to concrete data, direct quotes, and verifiable facts in the article."
        # Armar respuesta final
        agui_response = {
            "headline": claims_found[0]["headline"] if claims_found else "",
            "url": claims_found[0]["url"] if claims_found else "",
            "score": claims_found[0]["score"] if claims_found else 2,
            "score_label": claims_found[0]["report"] if claims_found else "Context Needed",
            "main_claim": clean_main_claim(claim),
            "detailed_analysis": brief_analysis(detailed_analysis),
            "verified_sources": [],
            "recommendation": media_quality_recommendation("High Trust" if claims_found else "Medium Risk"),
            "media_literacy_tip": factual_tip(),
            "processing_time": 0.0,
            "confidence_level": 60,
            "sources_checked": len(claims_found),
            "original_source_label": "High Trust" if claims_found else "Medium Risk",
            "original_source_url": original_url,
            "verified_sources_label": "High Trust" if claims_found else "Medium Risk",
            "perplexity_used": perplexity_used
        }
        print(f"[AGUI] Perplexity Sonar used: {perplexity_used}")
        return agui_response

    def perplexity_sonar_search(query, api_key, domains=None):
        """
        Realiza una búsqueda en Perplexity Sonar restringida a dominios si se proveen, usando search_domain_filter.
        """
        url = "https://api.perplexity.ai/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "sonar-reasoning-pro",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": query}
            ]
        }
        if domains:
            # Limitar a máximo 10 dominios, usar solo el dominio base sin https ni www
            payload["search_domain_filter"] = [d.replace("https://","").replace("http://","").replace("www.","").split("/")[0] for d in domains][:10]
        resp = requests.post(url, json=payload, headers=headers, timeout=20)
        if resp.status_code == 200:
            # El resultado relevante está en response["choices"][0]["message"]["content"]
            try:
                return resp.json()["choices"][0]["message"]["content"]
            except Exception:
                return ""
        return []
