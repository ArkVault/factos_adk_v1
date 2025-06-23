# Factos: Multi-Agent Shield Against Misinformation  
## ADK Project — Automated News Truth Verification System

---

### Overview

**Factos** is a smart, efficient multi-agent system built using the Agent Development Kit (ADK) to automate the verification of news articles. It extracts the main factual claim from a user-submitted article, compares it to a corpus of trusted fact-checking databases, and returns a structured misinformation score and explanation.

Misinformation is one of the greatest challenges of our era. It distorts public understanding, undermines science and journalism, threatens democratic institutions, and amplifies polarization. As digital content multiplies and traditional gatekeeping structures dissolve, misinformation spreads faster than it can be verified by humans. The need for scalable, explainable tools that can process and assess claims in real time is no longer optional—it's essential.

Factos addresses this challenge through a modular multi-agent architecture. Each agent specializes in a specific task in the fact-checking pipeline: content scraping, claim extraction, semantic matching, scoring, and formatting. The system uses asynchronous agent-to-agent (A2A) messaging and can be deployed as loosely coupled microservices, enabling horizontal scalability and clear reasoning traceability.

By combining lightweight NLP models, local vector similarity search, and minimal-token logic, Factos is optimized for cost-efficient, explainable misinformation detection in real-world deployments.

---

### Project Goals

- Automate verification of user-submitted news articles
- Extract the central factual claim using NLP
- Match extracted claims to trusted static and real-time fact-checking sources
- Return a structured misinformation score (0–3) with explanation and references
- Provide a response formatted for frontend integration via the AG-UI protocol

---

### Multi-Agent Architecture

The Factos system is composed of autonomous, asynchronous agents that communicate using defined message schemas. Each agent handles one core task in the verification pipeline.

#### Agents:

1. **SmartScraperAgent**  
   - Validates input URLs (HTTPS, accessible, known domains)  
   - Uses Firecrawl to extract structured article metadata and content  
   - Outputs: headline, byline, publish date, and article body  

2. **ClaimExtractorAgent**  
   - Applies NLP to extract a concise, token-limited factual claim  
   - Uses transformer-based sentence ranking (e.g., DistilBERT, MiniLM)  

3. **FactCheckMatcherAgent**  
   - Matches the extracted claim to verified claims using vector search  
   - Uses Faiss or Chroma to perform cosine similarity comparison  
   - Supports optional integration with real-time fact-checking APIs  

4. **TruthScorerAgent**  
   - Assigns a misinformation score (0 = True, 3 = False)  
   - Adds label (e.g., Misleading, Context Needed), source links, and rationale  

5. **ResponseFormatterAgent**  
   - Formats the complete result for compatibility with the AG-UI protocol  
   - Ensures structured response for display or downstream use

---

### Directory Structure

