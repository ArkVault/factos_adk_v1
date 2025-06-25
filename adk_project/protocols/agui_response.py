"""
Protocolo AG-UI para respuesta final
Formato esperado por el frontend AG-UI basado en la imagen de referencia
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class VerifiedSource:
    """Fuente verificada con enlace y descripción"""
    name: str
    url: str
    description: Optional[str] = None

@dataclass
class SourceCredibility:
    """Credibilidad de la fuente original"""
    label: str  # "Medium Risk", "High Trust", etc.
    risk_level: str  # "Medium", "Low", "High"
    domain: str

@dataclass
class AnalysisStats:
    """Estadísticas del análisis"""
    processing_time: float  # En segundos (ej: 2.3s)
    sources_checked: int    # Número de fuentes verificadas (ej: 6)
    confidence_level: int   # Porcentaje de confianza (ej: 94%)

@dataclass
class AGUIResponse:
    """
    Respuesta estructurada para el frontend AG-UI.
    Coincide exactamente con la estructura mostrada en la imagen.
    """
    # Información principal del artículo
    headline: str                    # "Study Shows Coffee Prevents Cancer in 90% of Cases"
    url: str                        # URL del artículo original
    source_domain: str              # "example-health-news.com"
    
    # Resultado del fact-check
    score: int                      # 1-5 donde 5 es completamente verdadero
    score_label: str               # "False", "Mostly False", "Mixed", "Mostly True", "True"
    score_fraction: str            # "3/3 • Completely false"
    
    # Análisis detallado
    main_claim: str                # El claim principal extraído
    detailed_analysis: str         # Análisis detallado de la veracidad
    
    # Fuentes verificadas
    verified_sources: List[VerifiedSource]  # Lista de fuentes que verifican/contradicen
    verified_sources_label: str             # "High Trust"
    match_type: str                         # "direct", "derivative", "tangential"
    
    # Recomendación y educación
    recommendation: str            # "Correction: Coffee contains compounds..."
    media_literacy_tip: str       # "Be wary of headlines claiming dramatic health benefits..."
    
    # Credibilidad de la fuente original
    source_credibility: SourceCredibility
    
    # Estadísticas del análisis
    analysis_stats: AnalysisStats
    
    # Agentes activos (para debugging/transparencia)
    active_agents: List[Dict[str, Any]] = None
    
    # Acciones rápidas
    quick_actions: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización JSON"""
        return {
            "headline": self.headline,
            "url": self.url,
            "source_domain": self.source_domain,
            "score": self.score,
            "score_label": self.score_label,
            "score_fraction": self.score_fraction,
            "main_claim": self.main_claim,
            "detailed_analysis": self.detailed_analysis,
            "verified_sources": [
                {
                    "name": source.name,
                    "url": source.url,
                    "description": source.description
                } for source in self.verified_sources
            ],
            "verified_sources_label": self.verified_sources_label,
            "match_type": self.match_type,
            "recommendation": self.recommendation,
            "media_literacy_tip": self.media_literacy_tip,
            "source_credibility": {
                "label": self.source_credibility.label,
                "risk_level": self.source_credibility.risk_level,
                "domain": self.source_credibility.domain
            },
            "analysis_stats": {
                "processing_time": self.analysis_stats.processing_time,
                "sources_checked": self.analysis_stats.sources_checked,
                "confidence_level": self.analysis_stats.confidence_level
            },
            "active_agents": self.active_agents or [],
            "quick_actions": self.quick_actions or {}
        }
