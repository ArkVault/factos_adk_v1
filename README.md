Factos: Multi-Agent Shield Against Misinformation
##ADK Project: Multi-Agent News Truth Verification System

Overview
This project implements a smart, efficient multi-agent system for automated news truth verification using the ADK (Agent Development Kit). The system is designed to extract the main claim from a user-submitted news article, match it against trusted fact-checking databases, and return a detailed misinformation score and analysis. It is optimized for low token usage, minimal API calls, and scalable deployment (e.g., Vertex AI Agent Builder).

Project Goals
Automate the verification of news articles submitted by users.
Extract the core factual claim from each article using NLP.
Match claims against a local and real-time fact-checking corpus (Snopes, FactCheck.org, AP, CDC, etc.).
Return a structured misinformation score (0–3) with a visual and textual breakdown.
Integrate with the AG-UI protocol and the factos_factcheckMultiagent frontend.
Relevance
Misinformation is a growing problem in digital media. This project provides a scalable, automated solution to help users and organizations quickly assess the truthfulness of news content, reducing the spread of false or misleading information.

Multi-Agent Implementation
The system is composed of specialized agents, each responsible for a key step in the verification pipeline:

1. SmartScraperAgent
Validates the input URL (HTTPS, accessible, valid domain).
Scrapes minimal but meaningful content using Firecrawl.
Extracts headline, byline, publish date, and full text (with depth cap).
2. ClaimExtractorAgent
Identifies and extracts the main factual claim using lightweight NLP models (e.g., DistilBERT, MiniLM).
Returns a concise, token-limited claim string.
3. FactCheckMatcherAgent
Checks the extracted claim against a locally maintained, embedded fact-check corpus.
Searches verified claims using cosine similarity (e.g., Faiss or Chroma).
Optionally queries real-time fact-checking APIs.
4. TruthScorerAgent
Assigns a misinformation score (0–3) and label (True, False, Misleading, Context Needed).
Provides a detailed analysis and references to verified sources.
5. ResponseFormatterAgent
Packages the results into a structured response for the AG-UI frontend.
Ensures compatibility with the AG-UI protocol and MCP integration.
Directory Structure
/agents: Implementations of each agent (SmartScraperAgent, ClaimExtractorAgent, etc.)
/messages: A2A message definitions (ValidatedArticle, ExtractedClaim, etc.)
/protocols: AG-UI and A2A schemas
/deployment: Vertex AI configuration and update jobs
Tools & Technologies Used
ADK (Agent Development Kit): For agent orchestration and communication
Firecrawl: For efficient web scraping
NLP Models: DistilBERT, MiniLM (for claim extraction)
Vector Search: Faiss or Chroma (for claim matching)
Vertex AI Agent Builder: For scalable cloud deployment
Python: Main programming language
AG-UI Protocol: For frontend integration
Deployment
Designed for deployment on Vertex AI (see /deployment/vertex_ai.md)
Agents are grouped in containers for scalability and cost optimization
Asynchronous operation and resource limits for each agent
Weekly jobs for database updates and result caching
How It Works
The user submits a news article URL.
The SmartScraperAgent validates and scrapes the article.
The ClaimExtractorAgent extracts the main claim.
The FactCheckMatcherAgent matches the claim against trusted sources.
The TruthScorerAgent assigns a score and provides analysis.
The ResponseFormatterAgent formats the result for the frontend.
Next Steps
Implement base files for each agent and key messages.
Expand the fact-checking corpus and real-time API integrations.
Optimize for further cost and speed improvements.
