"""
Protocolo A2A para mensajes entre agentes
Define los tipos de mensajes y su flujo
"""

A2A_MESSAGE_TYPES = [
    'ValidatedArticle',
    'ExtractedClaim',
    'MatchResults',
    'ScoredResult'
]

MAX_PAYLOAD_TOKENS = 512
