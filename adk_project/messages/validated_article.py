"""
Mensaje ValidatedArticle
Contiene: url, headline, byline, publish_date, full_text
"""

from dataclasses import dataclass

@dataclass
class ValidatedArticle:
    url: str
    headline: str
    byline: str
    publish_date: str
    full_text: str
