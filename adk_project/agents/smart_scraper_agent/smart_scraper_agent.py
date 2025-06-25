from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from adk_project.agents.smart_scraper_agent.prompt import SCRAPER_PROMPT
from adk_project.utils.firecrawl import firecrawl_scrape_tool

firecrawl_tool = FunctionTool(firecrawl_scrape_tool)

class SmartScraperAgent(LlmAgent):
    def __init__(self):
        super().__init__(
            name="SmartScraperAgent",
            instruction=SCRAPER_PROMPT + "\nUtiliza la herramienta firecrawl_tool para extraer el contenido principal de la noticia.",
            description="Valida la URL y extrae contenido relevante usando Firecrawl.",
            output_key="validated_article",
            model="gemini-2.5-flash",
            tools=[firecrawl_tool]
        )

    async def run_async(self, ctx):
        url = ctx.session.state.get("input", "")
        if not url:
            ctx.session.state["validated_article"] = {"error": "No URL provided"}
            yield
            return
        # Llama a Firecrawl usando el tool
        result = await firecrawl_scrape_tool(url)
        # Si hay markdown, también lo guardamos como 'markdown' en validated_article
        if "markdown" in result:
            result["markdown"] = result["markdown"]
        ctx.session.state["validated_article"] = result
        yield
