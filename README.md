# SasyaAI (सस्य AI)
> **Every Indian farmer deserves a personal agricultural scientist in their pocket — one that knows their land, their history, their constraints, and their aspirations.**

SasyaAI is an enterprise-grade, hyperlocal, intelligent agricultural advisory platform. It builds a **Dynamic Digital Twin** for every farmer to synthesize siloed agricultural datasets (AgriStack ID, Soil Health Cards, IMD weather feeds, eNAM mandi prices, satellite imagery) and orchestrates a secure, multi-agent AI pipeline validated by a hard constraint solver.

---

## 🚀 Key Features & Accomplished Phases

* **Phase 0: Requirements Engineering** — Defined SRS parameters, customer personas, system glossary, and service SLAs. See [docs/SRS.md](file:///home/cherry/Projects/sasya/docs/SRS.md).
* **Phase 1 & 2: Core Platform & Infrastructure** — Created the shared `common` module, reverse proxy gateway, Aadhaar OTP authentication simulator, and farmer/user profiles.
* **Phase 3: Digital Twin Engine** — Version-controlled database snapshotting and transactional rollbacks to protect farmer logs.
* **Phase 4: Knowledge Platform** — Native `pgvector` semantic database similarity search and rule execution engines (weather indices & mandi volatility rules).
* **Phase 5: Decoupled AI Services** — Orchestrated sub-agent pipelines (Planner, Vision, Geospatial, Monitoring) under an LLM-based intent router.
* **Phase 6: The Decision Engine** — **Google OR-Tools** GLOP linear solver evaluating water limits, capital costs, and land capacities to optimize crop mixes.
* **Phase 7: Farmer UX Portal** — Premium glassmorphic React dashboard web client featuring guided user onboarding, interactive SVG maps, and sandbox widgets.
* **Phase 8: DevOps & Production** — Provisioned AWS EKS VPC architectures using Terraform and metrics monitoring via Prometheus.
* **Phase 9: AI Validation** — SHAP explanation indicators, decision DAG structures, and human-in-the-loop escalation routing.

---

## 🛠️ Tech Stack

* **Frontend**: React.js, Vite, Lucide icons, HSL-tailored vanilla CSS.
* **Backend Framework**: FastAPI (Python 3.11+).
* **Database**: PostgreSQL with `pgvector` extension.
* **Cache**: Redis.
* **Math Solver**: Google OR-Tools (GLOP Linear Solver).
* **DevOps**: Docker, Docker Compose, Terraform, Helm, Prometheus.

---

## 🚦 Getting Started & Local Development

### 1. Build and Run the Stack
To boot all microservices, databases, cache, agent managers, and the React frontend client, navigate to the `infra/` directory and execute:
```bash
docker compose up -d --build
```

### 2. Port Mappings
Once booted, the services are exposed on the following local ports:
* **Frontend Web Dashboard**: [http://localhost:3000](http://localhost:3000)
* **API Gateway**: [http://localhost:8000](http://localhost:8000)
* **Databases**: PostgreSQL (`5432`), Redis (`6379`)
* **Backend Services**: Auth (`8001`), User (`8002`), Farmer (`8003`), Digital Twin (`8004`), Knowledge (`8005`), Decision Engine (`8006`).
* **Agents**: Orchestrator (`8010`), Planner (`8011`), Vision (`8012`), Geospatial (`8013`), Monitoring (`8014`).

### 3. Run Integration Tests
To run all 12 integration tests validating routing, OTP issuance, dynamic twin versions, RAG pgvector searches, OR-Tools optimization, and agent synthesis:
```bash
pytest testing/integration/test_core.py
```

### 4. Run AI Validation Pipeline
To run the explainability, SHAP values, and expert escalation router evaluations:
```bash
python testing/evaluation/explainability.py
```