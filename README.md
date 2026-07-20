# SasyaAI
> **Every Indian farmer deserves a personal agricultural scientist in their pocket — one that knows their land, their history, their constraints, and their aspirations.**

SasyaAI is an enterprise-grade, hyperlocal, intelligent agricultural advisory platform. It builds a **Dynamic Digital Twin** for every farmer to synthesize siloed agricultural datasets (AgriStack, Soil Health Cards, IMD weather, eNAM prices, satellite imagery) and orchestrates a secure, multi-agent AI pipeline validated by a hard constraint solver.

---

## 🚀 Project Navigation

### 📋 Documentation & Phase 0 Deliverables
All initial Software Requirements Specifications and journeys are located in the [docs/](file:///home/cherry/Projects/sasya/docs/) directory:
* **[docs/SRS.md](file:///home/cherry/Projects/sasya/docs/SRS.md)** — Software Requirements Specification covering stakeholders, constraints, compliance, and user flows.
* **[docs/UserStories.md](file:///home/cherry/Projects/sasya/docs/UserStories.md)** — Detailed user stories for farmers, extension officers, and system administrators.
* **[docs/AcceptanceCriteria.md](file:///home/cherry/Projects/sasya/docs/AcceptanceCriteria.md)** — Technical acceptance criteria, SLAs, and performance metrics.
* **[docs/Glossary.md](file:///home/cherry/Projects/sasya/docs/Glossary.md)** — Definitions of domain-specific agricultural terms, technical stacks, and regulation names.

### 🗺️ Implementation Roadmaps
* **[implementation.md](file:///home/cherry/Projects/sasya/implementation.md)** — The 9-phase execution blueprint guiding the project architecture, features, testing, and deployment.

---

## 🛠️ Architecture Overview
SasyaAI is organized as a decoupled, microservices-based system:
1. **Presentation Layer:** React Native Mobile (with edge-based quantised YOLOv8 for offline pest detection), React Web Dashboards, and Twilio IVR voice integrations.
2. **API Gateway:** Kong Gateway handling secure OAuth 2.0 validation, TLS terminations, and KEDA-driven rate limiting.
3. **Orchestrator & Agents:** An LLM-powered router coordinating tasks between dedicated sub-agents (Planning, Vision, Geospatial, Monitoring).
4. **Constraint Engine:** **Google OR-Tools** mathematical solver enforcing budgets, safety envelopes, and scheme regulations.
5. **Data Layer:** PostgreSQL with PostGIS extension for geo-spatial spatial analysis, pgvector for RAG document embeddings, MongoDB for transactional logs, and Redis for session cache.