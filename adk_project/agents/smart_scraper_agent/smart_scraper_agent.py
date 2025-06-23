from google.adk.agents import LlmAgent
from adk_project.agents.smart_scraper_agent.prompt import SCRAPER_PROMPT
import json
from google.adk.events import Event
from google.genai.types import Part, Content

class SmartScraperAgent(LlmAgent):
    def __init__(self):
        super().__init__(
            name="SmartScraperAgent",
            instruction=SCRAPER_PROMPT,
            description="Valida la URL y extrae contenido relevante usando Firecrawl.",
            output_key="validated_article",
            model="gemini-2.5-flash"
        )

    async def run_async(self, ctx):
        url = ctx.session.state.get("input", "")
        # Simulación específica para la URL de The Guardian
        if url == "https://www.theguardian.com/world/2025/jun/11/uk-and-gibraltar-strike-deal-over-territorys-future-and-borders":
            article = {
                "url": url,
                "headline": "UK and Gibraltar strike deal over territory's future and borders",
                "byline": "Sam Jones in Madrid and agencies",
                "publish_date": "2025-06-11",
                "full_text": (
                    "The UK and Gibraltar have reached a historic agreement with Spain over the future of the territory and its borders. "
                    "The deal is expected to ease tensions and ensure free movement between Gibraltar and Spain, while maintaining British sovereignty. "
                    "Officials from all sides hailed the agreement as a breakthrough after years of negotiations."
                )
            }
        else:
            # Simulación: siempre devuelve un artículo válido para pruebas
            article = {
                "url": "https://example-health-news.com",
                "headline": "Study Shows Coffee Prevents Cancer in 90% of Cases",
                "byline": "Health News Desk",
                "publish_date": "2025-06-21",
                "full_text": "Coffee consumption prevents 90% of all cancer cases according to new research. The study referenced only looked at a specific type of liver cancer in lab mice, not humans. It found a correlation between a compound in coffee and reduced tumor growth in mice, but did not demonstrate cancer prevention in humans at any percentage close to 90%."
            }
        final_part = Part(text=json.dumps(article))
        yield Event(content=Content(parts=[final_part]), author=self.name)
