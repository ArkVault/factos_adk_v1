"""
Mensaje ExtractedClaim
Contiene: claim, tokens_used
"""

from dataclasses import dataclass

@dataclass
class ExtractedClaim:
    claim: str
    tokens_used: int
