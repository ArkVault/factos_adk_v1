# Factos: Multi-Agent Shield Against Misinformation  
## ADK Project — Automated News Truth Verification System

![1](https://github.com/user-attachments/assets/95699079-9eba-4004-837b-91794ec310ad)

---
Misinformation has emerged as one of the most critical challenges of our time, threatening the fabric of informed societies and public discourse. With the growth of false news, distinguishing facts from fake information has become increasingly complex. The rapid spread of false information, coupled with sophisticated techniques for creating and distributing misleading content, demands innovative solutions leveraging artificial intelligence.

### Overview

**Factos** is a  multi-agent system built using the Agent Development Kit (ADK) to automate the verification of news articles. It extracts the main factual claims from a user-submitted article, compares it to a corpus of trusted fact-checkers, and returns a structured misinformation score and a evaluation of the claims, leveraging Gemini 2.5 Flash model for performace annd efficiency.

Misinformation is one of the greatest challenges of our era. It distorts public understanding, undermines science and journalism, threatens democratic institutions, and amplifies polarization. As digital content multiplies and traditional gatekeeping structures dissolve, misinformation spreads faster than it can be verified by humans. The need for scalable, explainable tools that can process and assess claims in real time is no longer optional—it's essential.

Factos addresses this challenge through a modular multi-agent architecture. Each agent specializes in a specific task in the fact-checking pipeline: content scraping, claim extraction, semantic matching, scoring, and formatting. The system uses asynchronous agent-to-agent (A2A) messaging and can be deployed as loosely coupled microservices, enabling horizontal scalability and clear reasoning traceability.




---

### Project Goals

- Automate verification of user-submitted news articles
- Extract the central factual claim using NLP
- Match extracted claims to trusted static and real-time fact-checking sources
- Return a structured misinformation score (0–3) with explanation and references
- Provide a response formatted for frontend integration via the AG-UI protocol

---

### Multi-Agent Architecture

The Factos is an asynchronous multi-agent pipeline in which each autonomous agent performs a specific stage of the fact-checking process—starting with URL validation and article scraping, then claim extraction, semantic matching, misinformation scoring, and finally formatting the result for UI consumption. Although the logical data flow is sequential, the architecture is event-driven: agents communicate via structured message allowing each agent to process tasks independently as messages arrive, making it highly adaptable for real-time, explainable misinformation detection.

![Captura de pantalla 2025-06-22 a la(s) 8 31 09 p m](https://github.com/user-attachments/assets/6f8a4181-d757-42bf-924f-bb06935f4276)


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

![architecture](https://github.com/user-attachments/assets/3e329cb1-0458-402f-ab2f-b6439c7e4e29)

---

### Directory Structure
/agents → Full agent implementations:
- SmartScraperAgent
- ClaimExtractorAgent
- FactCheckMatcherAgent
- TruthScorerAgent
- ResponseFormatterAgent


/protocols → AG-UI frontend protocol definitions 
/deployment → Vertex AI and container deployment configurations



---

### Toolbox

A selection of libraries and frameworks used across the system:

**Core Architecture:**
- **Agent Development Kit (ADK)** – Agent design, messaging, and orchestration
- **Pydantic** – Message schema validation and serialization
- **FastAPI** – Lightweight service layer for agent endpoints (optional)
- **Firecrawl** – Token-efficient web scraping with structured content extraction
- **Faiss / Chroma** – High-performance vector databases for semantic matching

**NLP Models:**
- **DistilBERT** – Lightweight transformer for claim classification and scoring
- **MiniLM** – Used for sentence embedding and similarity comparison

**Deployment and Infrastructure:**
- **Vertex AI Agent Builder** – Containerized deployment and scaling
- **Cloud Scheduler / Cloud Functions** – Fact database refresh and cache priming
- **Docker** – Agent containerization for deployment

**Integration:**
- **AG-UI Protocol** – Structured frontend response format for display and feedback
- **MCP (Model Context Protocol)** – Optional backend integration layer

---

### Deployment

Factos is optimized for deployment as modular cloud-native services. Each agent can run independently or grouped in containers.

- Deployment targets: **Vertex AI Agent Builder**, with support for other Kubernetes-based platforms
- Agents are containerized for cost-effective scaling
- Asynchronous design ensures resilience and fault isolation
- Scheduled background jobs for:
  - Weekly updates to the fact-checking corpus
  - Cache refresh for real-time performance improvements

---

### How It Works

1. The user submits a news article URL.
2. The **SmartScraperAgent** scrapes and validates the article.
3. The **ClaimExtractorAgent** extracts the main factual statement.
4. The **FactCheckMatcherAgent** compares it with known verified claims.
5. The **TruthScorerAgent** assigns a score and adds contextual metadata.
6. The **ResponseFormatterAgent** formats the full response for the frontend.



prototype can be viewed here https://factoswebapp-arkvaults-projects-d96cac84.vercel.app/

---

### Next Steps

- [ ] Implement and test each agent’s base file
- [ ] Expand and diversify the fact-checking knowledge base,more factcheckers
- [ ] Integrate fallback strategies using multiple claim extractors
- [ ] Deploy early prototypes with limited real-time coverage  
- [ ] A browser tool or extension to evaluate in-window news sites


