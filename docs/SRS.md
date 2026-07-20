# Software Requirements Specification (SRS)
## Project: SasyaAI (Hyperlocal Intelligent Agricultural Advisory System)
**Document Version:** 1.0.0  
**Status:** Approved  
**Author:** Lead Requirements Engineer  
**Date:** July 20, 2026  

---

## 1. Executive Summary & Vision
SasyaAI is an enterprise-grade agricultural decision-intelligence platform built to provide every Indian farmer with a personalized agricultural scientist in their pocket. By integrating previously siloed datasets—including AgriStack, Soil Health Cards (SHC), Indian Meteorological Department (IMD) weather data, and electronic National Agriculture Market (eNAM) prices—into a dynamic Digital Twin, SasyaAI delivers verified, explainable, and localized advisory in the farmer's native language.

The vision is to eliminate the information asymmetry faced by smallholder and marginal farmers, enabling data-driven cropping choices, early pest detection, water conservation, and frictionless access to government benefits.

---

## 2. Product Goals
* **Yield Improvement:** Increase average crop yield by 15–20% via precision planning and crop variety matching.
* **Input Cost Reduction:** Reduce fertilizer and pesticide expenditure by 10–15% through customized dosage calendars.
* **Pest Damage Mitigation:** Lower crop loss to pests and disease by 25–30% using real-time edge-based computer vision.
* **Water Use Efficiency:** Improve water conservation by 20% by matching crop planning with localized water tables.
* **Scheme Adoption Uplift:** Boost registration and benefits intake for eligible government schemes (e.g., PM-KISAN, PMFBY) by 30%.
* **Scalability:** Scale support to 200+ crops across 15 agro-climatic zones, at a target operational cost of $0.05–$0.07 per active farmer per month.

---

## 3. Business & Technical Requirements

### 3.1 Business Requirements
* **BR-1 (SLA-Driven Advisory):** The advisory must update automatically whenever input data (weather anomalies, market price shocks) changes.
* **BR-2 (Scale and Cost Optimization):** Platform must scale to support 50,000 farmers in the initial Phase 1 PoC, expanding to millions, keeping infrastructure footprint low.
* **BR-3 (B2B Commercialization):** The platform must expose secure API endpoints for third-party integrations (crop insurers, banks, FPOs, and input suppliers).
* **BR-4 (Expert Escalation):** Low-confidence AI outputs must automatically queue for manual verification by human Key Account Managers (KAMs) or agricultural extension officers.

### 3.2 Technical Requirements
* **TR-1 (Microservices Architecture):** The system must be decoupled into independent, stateless microservices communicating via an API Gateway and Apache Kafka.
* **TR-2 (Dynamic Digital Twin):** The database must store and update geospatial boundaries, soil properties, financials, and crop cycles with version history.
* **TR-3 (Hybrid DB Strategy):** PostgreSQL/PostGIS for transactional GIS queries; pgvector for RAG embeddings; MongoDB for audit logging; Redis for low-latency session caching.
* **TR-4 (Edge Computer Vision):** Pest diagnosis must run offline via quantised YOLOv8 on-device model files for rural connectivity.
* **TR-5 (Explainability Pipeline):** Every recommendation must generate a causal Directed Acyclic Graph (DAG) detailing *why* the advice was generated.

---

## 4. Stakeholders & User Personas

### 4.1 Stakeholder Matrix
* **Primary Beneficiaries:** Smallholder and marginal farmers (< 2 hectares).
* **Field Extension Officers:** Government/NGO extension workers validating soil tests and crop advisories.
* **FPO Managers:** Farmer Producer Organization heads coordinating input sourcing and collective logistics.
* **Domain Experts:** Agricultural scientists reviewing low-confidence anomalies.
* **Policymakers:** Government departments seeking real-time crop yields, stress indices, and disease trends.

### 4.2 User Personas

#### Persona A: Rajesh Kumar (Smallholder Smartphone User)
* **Demographics:** 42 years old, resides in Gorakhpur, UP. Operates 1.5 hectares of land.
* **Tech Profile:** Uses an entry-level Android smartphone. Comfortable with WhatsApp/YouTube but has low text-literacy.
* **Needs:** Localized Hindi voice inputs and output alerts. Simple visual guides for crop disease.
* **Constraints:** Poor mobile network in fields, high vulnerability to erratic weather, high input cost sensitivity.

#### Persona B: Lakshmi Bai (Marginal Feature Phone User)
* **Demographics:** 51 years old, resides in Anantapur, AP. Operates 0.8 hectares of dry land.
* **Tech Profile:** Uses a basic feature phone (no internet). No smartphone access.
* **Needs:** Advisory updates and scheme alerts delivered in Telugu via automated IVR voice calls or SMS.
* **Constraints:** High water scarcity, low awareness of central schemes, entirely dependent on rainfall.

#### Persona C: Vikram Rathore (Agricultural Extension Officer)
* **Demographics:** 29 years old, manages 8 villages in Nizamabad, Telangana.
* **Tech Profile:** Tech-savvy, uses laptop and high-end mobile.
* **Needs:** Unified dashboard to monitor crop health, soil moisture maps, and track pending disease alerts.
* **Constraints:** High caseload (500+ farmers), requires auditable reasoning before endorsing advice.

---

## 5. Functional Requirements

### 5.1 Dynamic Digital Twin Engine
* **FR-1.1 (Identity Linkage):** System shall map every profile to a unique AgriStack ID, containing verified land coordinates.
* **FR-1.2 (Dataset Fusion):** System shall merge Soil Health Cards, live weather feeds (IMD), daily market prices (eNAM), and satellite imagery (Sentinel-2) into the twin.
* **FR-1.3 (Versioning & Rollback):** System shall maintain a temporal database audit trail. Any change to crop state, financials, or soil parameters must create a new version.
* **FR-1.4 (Refresh Latency):** Weather and market price updates must synchronize with the Digital Twin within 15 minutes of release.

### 5.2 Multi-Agent Orchestration & Core Agents
* **FR-2.1 (LLM Router):** The Orchestrator LLM shall parse incoming user text/voice queries and route tasks dynamically to sub-agents.
* **FR-2.2 (Planning Agent):** Shall compute optimized crop calendars and identify matching government schemes.
* **FR-2.3 (Vision Agent):** Shall classify crop pests/diseases from uploaded images, returning a severity rating (0-5) and localized mitigation plan.
* **FR-2.4 (Geospatial Agent):** Shall calculate parcel-level NDVI, NDWI (water stress), and canopy health using satellite imagery.
* **FR-2.5 (Monitoring Agent):** Shall run background checks on weather risk indicators (frost, dry-spells) and trigger proactive alerts.

### 5.3 Hard Constraint Verification Engine
* **FR-3.1 (Google OR-Tools Solver):** Every agricultural planner recommendation must pass through an integer programming solver.
* **FR-3.2 (Resource Budgeting):** The solver must invalidate recommendations that exceed the farmer's water budget or soil safety thresholds (e.g., maximum NPK nitrogen toxicity limits).
* **FR-3.3 (Scheme Validation):** Automatically check regulatory government criteria before recommending a scheme.

### 5.4 Multilingual Delivery & Explainability
* **FR-4.1 (Multilingual Pipeline):** Support voice-to-text input (ASR) and text-to-voice output (TTS) in 10+ regional Indian languages (Hindi, Tamil, Telugu, Marathi, Bengali, Kannada, Odia, Gujarati, Malayalam, Punjabi).
* **FR-4.2 (Causal Reasoning Graphs):** The system shall output explainable reasoning chains using SHAP and decision DAGs (e.g., *"We recommend crop X because your soil nitrogen is low and the monsoon delay probability is >60%"*).

---

## 6. Non-Functional Requirements

### 6.1 Performance & Scalability
* **NFR-1.1 (Latency):** API Gateway response times must be < 500ms for cached queries.
* **NFR-1.2 (Agent Processing):** End-to-end agent query processing (including LLM generation) must complete within 3 seconds.
* **NFR-1.3 (Concurrency):** System must handle 5,000 concurrent active voice/data sessions without degradation.
* **NFR-1.4 (Scale):** Infrastructure must support horizontal autoscaling via Kubernetes Event-Driven Autoscaling (KEDA) based on CPU/Memory and queue depth (Kafka lag).

### 6.2 Availability & Reliability
* **NFR-2.1 (Uptime):** System must achieve 99.9% availability during peak agricultural seasons (sowing/harvesting).
* **NFR-2.2 (Graceful Degradation):** In case of offline conditions or low bandwidth, the mobile app must fall back to local cached SQLite data and edge-based YOLOv8 diagnostics.
* **NFR-2.3 (Data Durability):** Automated backups of the PostgreSQL Digital Twin store must execute daily with a Recovery Point Objective (RPO) of 24 hours.

### 6.3 Security & Compliance
* **NFR-3.1 (DPDP Act Compliance):** The platform must secure explicit Aadhaar-linked OTP consent before accessing or storing farmer registry data.
* **NFR-3.2 (Data Localisation):** All databases, logs, and cache stores must be hosted on cloud servers located physically within India.
* **NFR-3.3 (Access Control):** Microservice-to-microservice communication must be authenticated using OAuth 2.0 and mTLS.

### 6.4 Accessibility
* **NFR-4.1 (Voice First):** The user interface must allow complete workflow navigation (query submission, diagnosis, registration) using voice commands.
* **NFR-4.2 (Visual Simplicity):** The mobile UI must feature high-contrast elements, minimal text densities, and extensive iconography for low-literacy users.

---

## 7. Operational Journeys & Lifecycle

```
[Sowing Season Trigger] ──► [Twin Synchronises IMD/Soil Data]
                                       │
                                       ▼
                         [Planner Agent Computes Draft Plan]
                                       │
                                       ▼
                         [OR-Tools Validates Constraints]
                                       │
                                       ▼
                         [Advisory Delivered via Voice App/IVR]
```

### 7.1 Farmer Journey: Sowing Preparation & Advisory
1. Farmer Rajesh logs into the SasyaAI mobile app using voice authentication or Aadhaar OTP.
2. The Digital Twin synchronizes with the local soil health database, reflecting low phosphorus levels.
3. Rajesh requests a crop recommendation via Hindi voice input.
4. The Planner Agent suggests sowing Maize or Soybean.
5. The Google OR-Tools engine checks Gorakhpur's water table constraints and limits the recommendation to Maize.
6. The system sends a voice advisory explaining: *"Maize is recommended because your field has low water retention, and the sowing window closes in 5 days."*

### 7.2 Officer Journey: Incident Validation & Assistance
1. An anomaly in crop NDVI (vegetation index) is flagged by the Geospatial Agent for a specific plot.
2. Extension Officer Vikram receives a push alert on his dashboard.
3. Vikram visits the plot, takes a picture of the crop leaves via the SasyaAI mobile app.
4. The on-device YOLOv8 Vision Agent diagnoses *Fall Armyworm* with 88% confidence.
5. Because the confidence is above 85%, a localized mitigation plan is immediately generated and sent to the farmer's profile, logged under the digital twin audit.

### 7.3 Admin Journey: System & Rule Management
1. System Admin updates the pesticide toxicity thresholds in accordance with new Ministry of Agriculture guidelines.
2. The admin commits the change via the config panel.
3. The Monitoring Agent deploys the update to the constraint database, forcing all future crop plans to validate against the updated threshold.

---

## 8. Failure & Edge Cases

* **EC-1 (Soil Health Card Missing):** If a farmer's SHC database lookup returns null, the system must fall back to regional, district-level composite soil averages, indicating a warning flag in the explainability log.
* **EC-2 (Conflicting Constraints):** If the optimization problem is infeasible (e.g., severe drought results in a zero water budget, making all crop paths unviable), the OR-Tools solver will fail. The system must trigger a critical fallback routing to a human agri-expert KAM for immediate intervention.
* **EC-3 (Network Disconnection):** If connection drops during image upload, the application must store the image locally and automatically execute background sync and YOLOv8 inference as soon as connectivity resumes.
