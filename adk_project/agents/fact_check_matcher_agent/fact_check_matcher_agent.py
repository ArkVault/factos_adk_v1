from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from adk_project.agents.fact_check_matcher_agent.prompt import MATCHER_PROMPT
from adk_project.agents.fact_check_matcher_agent.factchecker_scraper import get_factchecker_claims
import os
import aiohttp

async def gemini_complete(prompt: str, model: str = "gemini-2.5-flash") -> str:
    """
    Wrapper eficiente para llamar a Gemini 2.5 vía API REST de Google Generative Language.
    Requiere la variable de entorno GOOGLE_API_KEY.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Falta GOOGLE_API_KEY en el entorno para usar Gemini.")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data, timeout=30) as resp:
            if resp.status == 200:
                result = await resp.json()
                return result["candidates"][0]["content"]["parts"][0]["text"]
            else:
                raise RuntimeError(f"Error en Gemini API: {resp.status}")

async def semantic_match_with_gemini(claim, factchecker_claims):
    """
    Usa Gemini 2.5 para hacer matching semántico entre el claim y los claims de fact-checkers.
    Devuelve el mejor match semántico y una explicación.
    """
    if not factchecker_claims:
        return {"semantic_match": None, "explanation": "No hay claims de fact-checkers para comparar."}
    prompt = (
        "Dado el siguiente claim extraído de una noticia y una lista de claims de fact-checkers, "
        "indica si alguno es equivalente, contradictorio o relacionado semánticamente. "
        "Devuelve el claim más relacionado, el tipo de relación (equivalente, contradictorio, relacionado, sin relación) "
        "y una breve explicación.\n\n"
        f"Claim original: {claim}\n"
        "Claims de fact-checkers:\n"
    )
    for i, fc in enumerate(factchecker_claims):
        texto = fc.get('main_claim') or fc.get('headline') or ''
        prompt += f"{i+1}. {texto}\n"
    prompt += "\nResponde en formato JSON: {\"match_index\": int, \"relacion\": str, \"explicacion\": str}"
    response = await gemini_complete(prompt)
    try:
        import json
        data = json.loads(response)
        idx = data.get("match_index")
        if idx is not None and 0 <= idx < len(factchecker_claims):
            match = factchecker_claims[idx]
        else:
            match = None
        return {"semantic_match": match, "relation": data.get("relacion"), "explanation": data.get("explicacion")}
    except Exception:
        return {"semantic_match": None, "explanation": "No se pudo parsear la respuesta de Gemini."}

async def factchecker_search_tool(main_claim: str):
    claims = await get_factchecker_claims(main_claim)
    # Si no hay matches con score alto, usar matching semántico
    high_score_matches = [c for c in claims if c.get('score', 0) >= 80]
    if high_score_matches:
        return claims
    # Matching semántico con Gemini
    sem_result = await semantic_match_with_gemini(main_claim, claims)
    # Adjuntar el resultado semántico al output
    return {"matches": claims, "semantic": sem_result}

factchecker_tool = FunctionTool(factchecker_search_tool)

class FactCheckMatcherAgent(LlmAgent):
    def __init__(self):
        super().__init__(
            name="FactCheckMatcherAgent",
            instruction=MATCHER_PROMPT + "\n\nUtiliza la herramienta factchecker_tool para buscar claims relevantes en tiempo real.",
            description="Busca la afirmación en la base local de fact-checks y en tiempo real en los principales fact-checkers.",
            output_key="match_results",
            tools=[factchecker_tool],
            model="gemini-2.5-flash"
        )

    async def run_async(self, ctx):
        claim = ctx.session.state.get("extracted_claim", {}).get("claim", "")
        if not claim:
            ctx.session.state["match_results"] = {"matches": []}
            yield
            return
        # Llama a la función real de scraping/API
        matches = await get_factchecker_claims(claim)
        # Si no hay matches con score alto, matching semántico
        high_score_matches = [c for c in matches if c.get('score', 0) >= 80]
        if high_score_matches:
            ctx.session.state["match_results"] = {"matches": matches}
        else:
            sem_result = await semantic_match_with_gemini(claim, matches)
            ctx.session.state["match_results"] = {"matches": matches, "semantic": sem_result}
        yield
