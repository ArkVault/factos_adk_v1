"""
Protocolo AG-UI para respuesta final
Formato esperado por el frontend AG-UI
"""

from dataclasses import dataclass
from typing import List

@dataclass
class AGUIResponse:
    score: int
    explanation: str
    sources: List[str]
    visuals: str
    hyperlinks: List[str]
