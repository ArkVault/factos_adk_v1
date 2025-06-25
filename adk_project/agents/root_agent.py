"""
RootAgent (Orquestador principal)
Agente LLM que decide inteligentemente cómo procesar URLs de noticias para verificación de hechos.
Basado en el tutorial de Google ADK: https://www.firecrawl.dev/blog/google-adk-multi-agent-tutorial
"""

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from adk_project.agents.smart_scraper_agent.smart_scraper_agent import SmartScraperAgent
from adk_project.agents.claim_extractor_agent.claim_extractor_agent import ClaimExtractorAgent
from adk_project.agents.fact_check_matcher_agent.fact_check_matcher_agent import FactCheckMatcherAgent
from adk_project.agents.truth_scorer_agent.truth_scorer_agent import TruthScorerAgent
from adk_project.agents.response_formatter_agent.response_formatter_agent import ResponseFormatterAgent
from adk_project.utils.firecrawl import firecrawl_scrape_tool

# Herramienta principal de scraping usando Firecrawl
async def web_scrape_tool(url: str) -> dict:
    """Extrae contenido de una URL usando Firecrawl para fact-checking."""
    try:
        result = await firecrawl_scrape_tool(url)
        return {
            "status": "success",
            "url": url,
            "content": result.get("markdown", ""),
            "metadata": result.get("metadata", {})
        }
    except Exception as e:
        return {
            "status": "error", 
            "url": url,
            "error": str(e)
        }

# Convertir función a herramienta ADK
web_scrape = FunctionTool(web_scrape_tool)

class RootAgent(LlmAgent):
    def __init__(self):
        super().__init__(
            name="FactCheckRootAgent",
            model="gemini-2.5-flash",
            description="Agente principal que orquesta la verificación de hechos de URLs de noticias usando agentes especializados.",
            instruction=(
                "Eres un verificador de hechos especializado que procesa URLs de noticias. "
                "Tu trabajo es coordinar agentes especializados para verificar la veracidad de las noticias. "
                "\n\nAl iniciar, revisa si hay una URL en el estado de la sesión (session.state['input']). "
                "Si hay una URL:\n"
                "1. Primero usa 'web_scrape_tool' para extraer el contenido de esa URL\n"
                "2. Delega a 'claim_extractor_agent' para extraer el claim principal\n"
                "3. Delega a 'fact_check_matcher_agent' para buscar fact-checks relacionados\n"
                "4. Delega a 'truth_scorer_agent' para evaluar la veracidad\n"
                "5. Delega a 'response_formatter_agent' para formatear la respuesta final\n"
                "\nSi no hay URL en el estado de la sesión, pide al usuario que proporcione una URL de noticia para verificar."
            ),
            tools=[web_scrape],
            sub_agents=[
                SmartScraperAgent(),
                ClaimExtractorAgent(), 
                FactCheckMatcherAgent(),
                TruthScorerAgent(),
                ResponseFormatterAgent()
            ]
        )
    
    async def run_async(self, ctx):
        """Override para manejar URLs desde el estado de la sesión"""
        
        # Verificar si hay una URL en el estado de la sesión
        url = ctx.session.state.get("input", "")
        
        if url and url.startswith(("http://", "https://")):
            print(f"[RootAgent] Procesando URL desde sesión: {url}")
            
            # Primero extraer contenido con Firecrawl
            print("[RootAgent] Paso 1: Extrayendo contenido con Firecrawl...")
            try:
                scrape_result = await web_scrape_tool(url)
                if scrape_result.get("status") == "success":
                    ctx.session.state["validated_article"] = {
                        "success": True,
                        "data": {
                            "markdown": scrape_result.get("content", ""),
                            "metadata": scrape_result.get("metadata", {})
                        }
                    }
                    print("[RootAgent] ✅ Contenido extraído exitosamente")
                else:
                    print(f"[RootAgent] ❌ Error extrayendo contenido: {scrape_result.get('error')}")
            except Exception as e:
                print(f"[RootAgent] ❌ Excepción extrayendo contenido: {e}")
            
            # Delegar a los sub-agentes secuencialmente
            print("[RootAgent] Paso 2: Delegando a sub-agentes...")
            
            for sub_agent in self.sub_agents:
                print(f"[RootAgent] Ejecutando {sub_agent.__class__.__name__}...")
                try:
                    async for event in sub_agent.run_async(ctx):
                        yield event
                except Exception as e:
                    print(f"[RootAgent] Error en {sub_agent.__class__.__name__}: {e}")
            
            print("[RootAgent] ✅ Pipeline completado")
        
        else:
            # No hay URL válida, ejecutar comportamiento normal
            async for event in super().run_async(ctx):
                yield event
