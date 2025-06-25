# Factos Agents

Sistema de agentes de fact-checking basado en Google ADK que verifica la veracidad de noticias y artículos web.

## Características

- **Extracción de Claims**: Extrae afirmaciones principales usando NLP y Firecrawl
- **Matching con Fact-checkers**: Busca en sitios de fact-checking reconocidos  
- **Puntuación de Veracidad**: Evalúa la credibilidad usando múltiples fuentes
- **Respuestas Estructuradas**: Formatea respuestas para interfaces AG-UI

## Tecnologías

- Google ADK 1.4.2 para agentes de IA
- Firecrawl para web scraping
- FastAPI para la API REST
- Python 3.12+

## Instalación

```bash
pip install -r requirements.txt
```

## Configuración

Crear archivo `.env` con las API keys necesarias:

```
GOOGLE_API_KEY=tu_api_key
FIRECRAWL_API_KEY=tu_api_key  
GOOGLE_FACTCHECK_API_KEY=tu_api_key
PERPLEXITY_API_KEY=tu_api_key
```

## Uso

```bash
uvicorn adk_project.api.main:app --host 0.0.0.0 --port 8080
```

## Docker

```bash
docker build -t factos-agents .
docker run -p 8080:8080 factos-agents
```
