# Integración de Firecrawl como Servicio HTTP

## Requisitos
- Tener Firecrawl disponible como contenedor Docker o servicio HTTP.
- API key válida en el archivo `.env`:
  ```
  FIRECRAWL_API_KEY=tu_api_key_aqui
  ```

## Levantar el servicio Firecrawl

Si usas Docker:
```sh
docker run -p 3000:3000 firecrawl/firecrawl:latest
```
Esto expone Firecrawl en `http://localhost:3000`.

## Configuración del agente

El agente hace peticiones HTTP a Firecrawl usando la API key como header:
```python
import os
import aiohttp

async def firecrawl_scrape_tool(url: str):
    FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY")
    headers = {"Authorization": f"Bearer {FIRECRAWL_API_KEY}"} if FIRECRAWL_API_KEY else {}
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:3000/scrape",
            json={"url": url},
            headers=headers
        ) as resp:
            return await resp.json()
```

## Uso en el pipeline
- El agente invoca `firecrawl_scrape_tool(url)` para obtener el contenido estructurado de cualquier noticia.
- El resultado se usa en el pipeline de verificación y extracción de claims.

## Notas
- Asegúrate de que Firecrawl esté corriendo antes de ejecutar los tests o el pipeline.
- Si cambias el puerto o la URL del servicio, actualízalo en el código del agente.
