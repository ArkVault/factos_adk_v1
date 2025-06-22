"""
Mensaje MatchResults
Contiene: matches (lista de dicts con claim, source, confidence)
"""

from dataclasses import dataclass
from typing import List, Dict

@dataclass
class MatchResults:
    matches: List[Dict[str, object]]
