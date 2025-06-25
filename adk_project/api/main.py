from fastapi import FastAPI, HTTPException, status, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, validator
from typing import List, Any, Optional
from adk_project.agents.root_agent import RootAgent
from google.adk.sessions import Session, InMemorySessionService
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.run_config import RunConfig
import uuid
import asyncio
import time
import logging
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Factos Agents API",
    description="AI-powered fact-checking service using Google ADK",
    version="1.0.0"
)

# CORS middleware para permitir requests desde frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de datos mejorados
class NewsURL(BaseModel):
    url: HttpUrl
    
    @validator('url')
    def validate_url(cls, v):
        """Validar que la URL sea de un dominio de noticias válido"""
        url_str = str(v)
        # Lista de dominios de noticias comunes (expandible)
        valid_domains = [
            'apnews.com', 'reuters.com', 'bbc.com', 'cnn.com', 'theguardian.com',
            'nytimes.com', 'washingtonpost.com', 'wsj.com', 'npr.org', 'abc.com',
            'cbsnews.com', 'nbcnews.com', 'foxnews.com', 'politico.com', 'time.com',
            'newsweek.com', 'bloomberg.com', 'usatoday.com', 'latimes.com'
        ]
        
        # Permitir cualquier URL por ahora, pero logear si no es de un dominio conocido
        is_known_domain = any(domain in url_str.lower() for domain in valid_domains)
        if not is_known_domain:
            logger.warning(f"URL from unknown news domain: {url_str}")
        
        return v

class PredictRequest(BaseModel):
    instances: List[str]  # URLs como strings
    
    @validator('instances')
    def validate_instances(cls, v):
        if not v:
            raise ValueError("At least one URL must be provided")
        if len(v) > 5:  # Limitar a 5 URLs por request
            raise ValueError("Maximum 5 URLs allowed per request")
        return v

class VerifiedSourceModel(BaseModel):
    name: str
    url: str
    description: Optional[str] = None

class SourceCredibilityModel(BaseModel):
    label: str
    risk_level: str
    domain: str

class AnalysisStatsModel(BaseModel):
    processing_time: float
    sources_checked: int
    confidence_level: int

class FactCheckResult(BaseModel):
    """Resultado de fact-checking compatible con la interfaz AG-UI"""
    # Información principal del artículo
    headline: str
    url: str
    source_domain: str
    
    # Resultado del fact-check
    score: int
    score_label: str
    score_fraction: str
    
    # Análisis detallado
    main_claim: str
    detailed_analysis: str
    
    # Fuentes verificadas
    verified_sources: List[VerifiedSourceModel]
    verified_sources_label: str
    
    # Recomendación y educación
    recommendation: str
    media_literacy_tip: str
    
    # Credibilidad de la fuente
    source_credibility: SourceCredibilityModel
    
    # Estadísticas del análisis
    analysis_stats: AnalysisStatsModel
    
    # Información adicional
    active_agents: List[dict] = []
    quick_actions: dict = {}

class PredictResponse(BaseModel):
    predictions: List[FactCheckResult]
    processing_info: dict

# Endpoints básicos
@app.get("/")
async def root():
    """Endpoint raíz con información del servicio"""
    return {
        "service": "Factos Agents API",
        "description": "AI-powered fact-checking service using Google ADK",
        "version": "1.0.0 - Optimized",
        "status": "running",
        "endpoints": {
            "fact_check": "/fact-check",
            "predict": "/predict", 
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint para Cloud Run"""
    try:
        # Verificar que las variables de entorno críticas estén presentes
        required_vars = ["GOOGLE_API_KEY", "FIRECRAWL_API_KEY", "PERPLEXITY_API_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            return {
                "status": "unhealthy",
                "error": f"Missing environment variables: {missing_vars}",
                "timestamp": time.time()
            }
        
        return {
            "status": "healthy",
            "service": "factos-agents",
            "version": "1.0.0-optimized",
            "timestamp": time.time(),
            "uptime": "running"
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "error": str(e),
            "timestamp": time.time()
        }

# Health check endpoint
@app.get("/health-old", tags=["health"])
def detailed_health_check():
    """Detailed health check with environment validation"""
    required_env_vars = [
        "GOOGLE_API_KEY", 
        "FIRECRAWL_API_KEY", 
        "GOOGLE_FACTCHECK_API_KEY", 
        "PERPLEXITY_API_KEY"
    ]
    
    env_status = {}
    all_env_ok = True
    
    for var in required_env_vars:
        value = os.getenv(var)
        env_status[var] = "configured" if value else "missing"
        if not value:
            all_env_ok = False
    
    return {
        "status": "healthy" if all_env_ok else "degraded",
        "environment_variables": env_status,
        "service": "Factos Agents API",
        "version": "1.0.0",
        "timestamp": time.time()
    }

@app.post("/predict", response_model=PredictResponse, tags=["fact-check"])
async def fact_check_news(request: PredictRequest):
    """
    Fact-check news articles from provided URLs
    
    This endpoint processes news URLs through the complete fact-checking pipeline:
    1. SmartScraperAgent: Validates and scrapes the URL
    2. ClaimExtractorAgent: Extracts main claims from the article
    3. FactCheckMatcherAgent: Searches fact-checking databases
    4. TruthScorerAgent: Scores the claims for truthfulness
    5. ResponseFormatterAgent: Formats the final response
    
    Args:
        request: PredictRequest containing list of news URLs
        
    Returns:
        PredictResponse with fact-check results for each URL
    """
    start_time = time.time()
    results = []
    processing_info = {
        "total_urls": len(request.instances),
        "processed_urls": 0,
        "failed_urls": 0,
        "start_time": start_time
    }
    
    logger.info(f"Processing {len(request.instances)} URLs for fact-checking")
    
    for i, url in enumerate(request.instances):
        try:
            logger.info(f"Processing URL {i+1}/{len(request.instances)}: {url}")
            
            # Validar URL individual
            try:
                news_url = NewsURL(url=url)
                validated_url = str(news_url.url)
            except Exception as e:
                logger.error(f"Invalid URL {url}: {e}")
                results.append(create_fact_check_result(
                    url=url,
                    processing_time=0.0,
                    error_info={
                        "score_label": "Invalid URL",
                        "detailed_analysis": f"Invalid URL provided: {str(e)}",
                        "recommendation": "Please provide a valid news URL",
                        "media_literacy_tip": "Always verify that URLs are from legitimate news sources"
                    }
                ))
                processing_info["failed_urls"] += 1
                continue
            
            # Crear sesión para el agente
            session = Session(
                id=str(uuid.uuid4()),
                app_name="factos-agents-production",
                user_id="api-user",
                state={"input": validated_url}
            )
            
            # Configurar agente con timeout
            agent = RootAgent()
            session_service = InMemorySessionService()
            ctx = InvocationContext(
                session=session,
                session_service=session_service,
                invocation_id=str(uuid.uuid4()),
                agent=agent,
                run_config=RunConfig()
            )
            
            # Ejecutar pipeline con timeout
            url_start_time = time.time()
            events = []
            
            try:
                # Timeout de 60 segundos por URL
                async with asyncio.timeout(60):
                    async for event in agent.run_async(ctx):
                        events.append(event)
                
                processing_time = time.time() - url_start_time
                
                # Extraer resultado
                agui_response = session.state.get("agui_response", {})
                
                if not agui_response or "error" in agui_response:
                    raise Exception("No valid response from fact-checking pipeline")
                
                # Asegurar que todos los campos requeridos están presentes
                result = create_fact_check_result(
                    agui_response=agui_response,
                    url=validated_url,
                    processing_time=processing_time
                )
                
                results.append(result)
                processing_info["processed_urls"] += 1
                
                logger.info(f"Successfully processed URL {url} in {processing_time:.2f}s")
                
            except asyncio.TimeoutError:
                logger.error(f"Timeout processing URL {url}")
                results.append(create_fact_check_result(
                    url=validated_url,
                    processing_time=60.0,
                    error_info={
                        "score_label": "Processing Timeout",
                        "detailed_analysis": "Processing timed out after 60 seconds",
                        "recommendation": "Try again later or check if the URL is accessible",
                        "media_literacy_tip": "Some sources may take longer to process due to complex content"
                    }
                ))
                processing_info["failed_urls"] += 1
                
        except Exception as e:
            logger.error(f"Error processing URL {url}: {str(e)}")
            results.append(create_fact_check_result(
                url=url,
                processing_time=0.0,
                error_info={
                    "score_label": "Processing Error",
                    "detailed_analysis": f"An error occurred while processing: {str(e)}",
                    "recommendation": "Please try again or contact support if the issue persists",
                    "media_literacy_tip": "Technical errors can occur when processing complex content"
                }
            ))
            processing_info["failed_urls"] += 1
    
    # Completar información de procesamiento
    total_time = time.time() - start_time
    processing_info.update({
        "total_processing_time": total_time,
        "average_time_per_url": total_time / len(request.instances) if request.instances else 0,
        "success_rate": processing_info["processed_urls"] / len(request.instances) if request.instances else 0,
        "end_time": time.time()
    })
    
    logger.info(f"Completed processing {len(request.instances)} URLs in {total_time:.2f}s")
    
    return PredictResponse(
        predictions=results,
        processing_info=processing_info
    )

# Endpoint para procesar una sola URL (conveniencia)
@app.post("/fact-check", response_model=FactCheckResult, tags=["fact-check"])
async def fact_check_single_url(url: NewsURL):
    """
    Fact-check a single news URL (convenience endpoint)
    """
    request = PredictRequest(instances=[str(url.url)])
    response = await fact_check_news(request)
    
    if not response.predictions:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process the URL"
        )
    
    return response.predictions[0]

# Endpoint de prueba que acepta GET y POST para debugging
@app.get("/test-fact-check", response_model=dict, tags=["debug"])
@app.post("/test-fact-check", response_model=dict, tags=["debug"])
async def test_fact_check_endpoint(url: str = Query(None), request_body: dict = Body(None)):
    """
    Endpoint de prueba para debugging - acepta tanto GET como POST
    """
    if url:  # GET request
        test_url = url
    elif request_body and "url" in request_body:  # POST request
        test_url = request_body["url"]
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se requiere 'url' como query parameter (GET) o en el body (POST)"
        )
    
    return {
        "test": "success",
        "received_url": test_url,
        "method": "GET or POST accepted",
        "cors_enabled": True,
        "ready_for_fact_check": True
    }

def create_fact_check_result(
    agui_response: dict = None,
    url: str = "",
    processing_time: float = 0.0,
    error_info: dict = None
) -> dict:
    """
    Crear un resultado de fact-check completo con todos los campos requeridos
    """
    from urllib.parse import urlparse
    
    # Extraer dominio de la URL
    try:
        parsed_url = urlparse(url)
        source_domain = parsed_url.netloc or "unknown"
    except:
        source_domain = "unknown"
    
    if error_info:
        # Caso de error
        return {
            "headline": error_info.get("headline", ""),
            "url": url,
            "source_domain": source_domain,
            "score": 0,
            "score_label": error_info.get("score_label", "Error"),
            "score_fraction": "0/10",
            "main_claim": "",
            "detailed_analysis": error_info.get("detailed_analysis", "An error occurred"),
            "verified_sources": [],
            "verified_sources_label": "N/A",
            "recommendation": error_info.get("recommendation", "Please try again"),
            "media_literacy_tip": error_info.get("media_literacy_tip", "Always verify information from multiple sources"),
            "source_credibility": {
                "label": "Unknown",
                "risk_level": "Unknown",
                "domain": source_domain
            },
            "analysis_stats": {
                "processing_time": processing_time,
                "sources_checked": 0,
                "confidence_level": 0
            },
            "active_agents": [],
            "quick_actions": {}
        }
    
    if not agui_response:
        agui_response = {}
    
    # Calcular score_fraction
    score = agui_response.get("score", 0)
    score_fraction = f"{score}/10"
    
    # Construir source_credibility
    source_credibility = agui_response.get("source_credibility", {})
    if not isinstance(source_credibility, dict):
        source_credibility = {}
    
    source_credibility_obj = {
        "label": source_credibility.get("label", "Unknown"),
        "risk_level": source_credibility.get("risk_level", "Unknown"),
        "domain": source_domain
    }
    
    # Construir analysis_stats
    analysis_stats = {
        "processing_time": processing_time,
        "sources_checked": agui_response.get("sources_checked", 0),
        "confidence_level": agui_response.get("confidence_level", 0)
    }
    
    return {
        "headline": agui_response.get("headline", ""),
        "url": agui_response.get("url", url),
        "source_domain": source_domain,
        "score": score,
        "score_label": agui_response.get("score_label", "Unknown"),
        "score_fraction": score_fraction,
        "main_claim": agui_response.get("main_claim", ""),
        "detailed_analysis": agui_response.get("detailed_analysis", ""),
        "verified_sources": agui_response.get("verified_sources", []),
        "verified_sources_label": agui_response.get("verified_sources_label", "N/A"),
        "recommendation": agui_response.get("recommendation", ""),
        "media_literacy_tip": agui_response.get("media_literacy_tip", ""),
        "source_credibility": source_credibility_obj,
        "analysis_stats": analysis_stats,
        "active_agents": agui_response.get("active_agents", []),
        "quick_actions": agui_response.get("quick_actions", {})
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)