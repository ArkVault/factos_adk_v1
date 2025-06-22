## 🧠 Project Title:
**Smart and Efficient Multi-Agent System for Verifying News Truth**

---

## 🎯 Project Goal
Design a multi-agent system using the **ADK (Agent Development Kit)** that automates the truth verification of user-submitted news articles. The system should extract the article’s core claim, match it against a trusted set of databases (Snopes, FactCheck.org, WHO, CDC, etc.), and return a **Misinformation Score (0–3)** with a visual + textual breakdown — while optimizing for **low token usage, minimal API calls, and scalable deployment using Vertex AI Agent Builder**.

This system must integrate with the frontend from the `factos_factcheckMultiagent` MCP and follow the **AG-UI protocol**.

---

## 🔍 Agent Roles (Cost-Optimized Architecture)
### Agent 1: `SmartScraperAgent`
- **Responsibilities**:
  - Validate the input URL (HTTPS, accessible, valid domain)
  - Scrape minimal but meaningful content using **Firecrawl**
  - Extract headline, byline, publish date, and full text (depth capped)

- **Efficiency Notes**:
  - Use a whitelist of known news domains to skip invalids early
  - Limit scrape depth and field extraction to save Firecrawl calls

---

### Agent 2: `ClaimExtractorAgent`
- **Responsibilities**:
  - Identify and extract the **main factual claim** using lightweight NLP models (DistilBERT, MiniLM)
  - Return a concise, token-limited claim string

- **Efficiency Notes**:
  - Apply 256-token cap on input content
  - Use pretrained transformers that prioritize semantic clarity at low compute cost

---

### Agent 3: `FactCheckMatcherAgent`
- **Responsibilities**:
  - Check the extracted claim against a **locally maintained, embedded fact-check corpus**
  - Search verified claims using cosine similarity (Faiss or Chroma)
  - Return matched claim(s), source(s), and relevance confidence

- **Efficiency Notes**:
  - Replace real-time API calls with weekly-updated embedded databases
  - Pre-index all known fact-check sources

---

### Agent 4: `TruthScorerAgent`
- **Responsibilities**:
  - Score the claim on a **0–3 misinformation scale**
    - 0 = Verified True
    - 1 = Context Needed
    - 2 = Misleading
    - 3 = False
  - Generate a short explanation and cite matched sources

- **Efficiency Notes**:
  - Use rule-based logic or few-shot prompting with static context
  - Avoid calling LLMs unless score confidence is below threshold

---

### Agent 5: `ResponseFormatterAgent`
- **Responsibilities**:
  - Format the results (score, explanation, sources, visuals) into JSON
  - Ensure output is ready for **AG-UI frontend protocol**
  - Minimize token use by sending only essential response data

- **Efficiency Notes**:
  - Return concise JSON with plain text + hyperlink references
  - Use AG-UI schema to eliminate frontend processing needs

---

## 🔁 A2A Communication Design
- Use **A2A (Agent-to-Agent)** messaging with lightweight schema
- Key messages:
  - `ValidatedArticle`
  - `ExtractedClaim`
  - `MatchResults`
  - `ScoredResult`
- Payload token size target: **<512 tokens per message**

---

## 🧩 Frontend Integration (MCP Reference)
- Leverage existing frontend from `factos_factcheckMultiagent`
  - URL input bar
  - Trigger button
  - Result renderer
- Use **AG-UI Interface Protocol** to deliver output with zero additional frontend coding

---

## 🚀 Vertex AI Deployment Strategy
- **Deployment Plan**:
  1. Container Group 1: `SmartScraperAgent`
  2. Container Group 2: `ClaimExtractorAgent` + `FactCheckMatcherAgent`
  3. Container Group 3: `TruthScorerAgent` + `ResponseFormatterAgent`
- Deploy using **Vertex AI Agent Builder Standard Tier** with scaling rules
- Schedule **weekly background jobs** to update embedded fact databases

- **Efficiency Notes**:
  - All agents run asynchronously with defined memory/CPU budgets
  - Use **cold start mode** for infrequent agents (like `MatcherAgent`)
  - Cache results of recent verifications to reduce re-processing

---

## 🔌 Data + External Services
- Use Firecrawl for content extraction (1–2 crawl depth max)
- Maintain local, embedded, and searchable versions of:
  - Snopes
  - FactCheck.org
  - AP Fact Check
  - WHO & CDC claims
- Use **embedding + Faiss search** over raw API calls

---

## 🔄 System Workflow Summary
1. User submits a URL on the frontend
2. `SmartScraperAgent` validates and scrapes the article
3. `ClaimExtractorAgent` identifies the main claim
4. `FactCheckMatcherAgent` finds the closest verified claim match
5. `TruthScorerAgent` assigns a misinformation score and summary
6. `ResponseFormatterAgent` packages result for frontend delivery

---

## ✅ Success Metrics
- <15 seconds total processing time per request
- ≤2,000 total tokens used per verification roundtrip
- 100% AG-UI frontend compatibility
- 3-agent deployment footprint max
- 80%+ claim match accuracy using embedded corpus

