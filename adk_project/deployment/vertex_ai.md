# Vertex AI Deployment

- Container Group 1: SmartScraperAgent
- Container Group 2: ClaimExtractorAgent + FactCheckMatcherAgent
- Container Group 3: TruthScorerAgent + ResponseFormatterAgent

## Notas
- Usar Standard Tier
- Definir reglas de escalado y jobs semanales para actualización de base de datos
- Todos los agentes deben correr asíncronos y con límites de recursos
- Cold start para agentes poco frecuentes
- Cache de resultados recientes
