# Repository Strategy & Directory Structure: SasyaAI

This document defines the repository organization, branching policy, and directory structure for **SasyaAI**.

---

## 1. Repository Strategy: Monorepo

SasyaAI uses a **Monorepo** strategy. A single git repository holds the source code for all microservices, mobile applications, web dashboards, infrastructure templates, and machine learning scripts. 

### Why Monorepo?
* **Unified Dependency Management:** Enables shared common utilities (e.g., database schemas, custom middleware, auth validators) without publishing packages to external registries.
* **Consistent CI/CD Pipelines:** Changes spanning multiple services (e.g., changing a gRPC contract between Orchestrator and Vision Agent) can be tested, reviewed, and deployed in a single pull request.
* **Simplified Local Setup:** Developers can spin up the entire system locally using a single `docker-compose.yml` file.

---

## 2. Directory Structure Tree

The folder structure below must be adhered to during the Phase 2 implementation and onwards:

```
sasya-ai/
├── .github/                   # CI/CD Workflows (GitHub Actions)
├── docs/                      # Requirements, Architecture, & Design Specs
│   ├── SRS.md
│   ├── UserStories.md
│   ├── AcceptanceCriteria.md
│   ├── Glossary.md
│   └── Architecture.md
│
├── backend/                   # Core Transactional Microservices
│   ├── gateway/               # Kong/FastAPI API Gateway
│   ├── auth-service/          # OAuth2 and Aadhaar OTP Auth Service
│   ├── user-service/          # Profile Management Service
│   ├── digital-twin/          # PostGIS Digital Twin Engine
│   ├── knowledge/             # pgvector RAG & Schemes Service
│   └── decision-engine/       # Google OR-Tools Constraint Service
│
├── agents/                    # Specialised AI Agents
│   ├── orchestrator/          # LLM Orchestrator Service
│   ├── planner/               # Crop & Scheme Planning Agent
│   ├── vision/                # YOLOv8 Pest/Disease Image Agent
│   ├── geospatial/            # Satellite Raster Processing Agent
│   └── monitoring/            # Celery Weather/Market Monitor Agent
│
├── common/                    # Shared python packages (internal dependencies)
│   ├── common/database/       # Base DB sessions & ORM classes
│   ├── common/security/       # JWT validators, encryption utils
│   ├── common/logging/        # JSON structured logging config
│   └── setup.py               # Setup configuration for local pip install
│
├── mobile/                    # React Native Expo Mobile App
│   ├── assets/                # Icons, local translation catalogs
│   ├── src/                   # React Native screens & state logic
│   └── App.js
│
├── frontend/                  # Web-based Portals (Officer, Admin)
│   ├── public/
│   ├── src/                   # React.js web application
│   └── package.json
│
├── infra/                     # Infrastructure as Code (IaC) & DevOps
│   ├── terraform/             # AWS resources configuration (VPC, EKS, RDS)
│   ├── helm/                  # K8s deploy manifests per service
│   │   ├── gateway/
│   │   ├── digital-twin/
│   │   └── parent-chart/
│   └── docker-compose.yml     # Local orchestration environment
│
├── testing/                   # Test suite beyond unit tests
│   ├── integration/           # Service-to-service API tests
│   └── performance/           # Locust load testing scripts
│
└── ml/                        # Machine Learning Notebooks & Datasets
    ├── training/              # YOLOv8 pest training scripts
    └── evaluation/            # Hallucination and accuracy verification
```

---

## 3. Directory Breakdown

### 3.1 `backend/` & `agents/`
Every subdirectory inside `backend/` and `agents/` is configured as a standalone service containing:
* `src/`: Application source code.
* `tests/`: Unit tests specific to that service.
* `Dockerfile`: Container image configuration.
* `requirements.txt`: Python package specifications.

### 3.2 `common/`
This folder contains shared code libraries used across Python services to avoid code duplication:
* Microservices import this library during container build via:
  ```dockerfile
  COPY common/ /app/common/
  RUN pip install -e /app/common/
  ```

### 3.3 `infra/`
* **`terraform/`**: Orchestrates VPCs, managed databases (RDS PostgreSQL, DocumentDB/MongoDB), caches (ElastiCache/Redis), and Kubernetes clusters.
* **`helm/`**: Chart configurations defining ingress policies, scaling markers (KEDA/HPA), environment variables, and vault secrets mappings.

---

## 4. Branching & Git Flow Strategy

1. **`main` Branch:** Protected branch containing production-ready code. Commits are blocked; changes must arrive via approved Pull Requests (PRs).
2. **`dev` Branch:** Integration branch. All feature branches merge here first to run nightly integration test suites.
3. **Feature Branches (`feat/`, `fix/`, `chore/`):** Short-lived branches spawned by developers (e.g., `feat/digital-twin-schema`, `fix/auth-token-validation`).
4. **CI Validation Gating:** A Pull Request merging into `dev` or `main` must:
   * Pass all unit tests inside changed subfolders.
   * Maintain code coverage of >= 80%.
   * Complete static analysis lint checks (`flake8`, `black`, `mypy`).
   * Pass API contract verification tests.
