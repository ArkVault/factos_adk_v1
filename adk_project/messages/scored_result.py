"""
Mensaje ScoredResult
Contiene: score (0-3), explanation, sources
"""

from dataclasses import dataclass
from typing import List

@dataclass
class ScoredResult:
    score: int
    explanation: str
    sources: List[str]
