# Glossary of Terms: SasyaAI

This document defines the key domain, technical, and regulatory terms utilized across the **SasyaAI** ecosystem.

---

## 1. Agricultural & Domain Terms

* **AgriStack:** A digital agricultural ecosystem initiated by the Ministry of Agriculture & Farmers Welfare (MoAFW), Government of India. It links land records, farmer registry databases, and unique identifiers to create a unified registry.
* **Soil Health Card (SHC):** A printed card issued by the government containing the status of 12 soil nutrients (Macro, Secondary, and Micro-nutrients) along with physical parameters like pH and Electrical Conductivity (EC). Used to recommend optimal fertilizer dosages.
* **eNAM (electronic National Agriculture Market):** A pan-India electronic trading portal which networks existing APMC (Agricultural Produce Market Committee) mandis to create a unified national market for agricultural commodities.
* **IMD (India Meteorological Department):** The primary national agency responsible for meteorological observations, weather forecasting, and seismology.
* **NPSS (National Pest Surveillance System):** An initiative of the Government of India providing labeled databases of regional agricultural pests, crop diseases, and corresponding chemical/biological treatment protocols.
* **FPO (Farmer Producer Organization):** A legal entity formed by primary producers (farmers) to leverage economies of scale in purchasing inputs, sharing machinery, and marketing produce.
* **Mandi:** A physical marketplace or trade center regulated by the APMC where agricultural produce is traded.
* **Kharif:** The autumn crop season in India, typically sown in June/July (onset of monsoons) and harvested in September/October (e.g., Rice, Maize, Cotton).
* **Rabi:** The spring crop season in India, typically sown in October/November (winter) and harvested in March/April (e.g., Wheat, Mustard, Gram).

---

## 2. Technical & Architectural Terms

* **Dynamic Digital Twin:** A virtual, real-time updated representation of a farmer's plot, combining static parameters (AgriStack ID, parcel boundary, soil health data) with dynamic elements (live weather, market prices, NDVI, finance ledger, historical crop yields).
* **Google OR-Tools:** An open-source software suite developed by Google for operations research, mathematical optimization, and solving linear programming, integer programming, and constraint satisfaction problems.
* **YOLOv8 (You Only Look Once v8):** A state-of-the-art computer vision model architecture optimized for object detection, segmentation, and classification, used in SasyaAI for local, edge-based crop disease diagnosis.
* **RAG (Retrieval-Augmented Generation):** An AI technique where an LLM retrieves factual articles, government scheme details, or scientific advisory guides from a database (often vector-based) and uses this context to ground its response, preventing hallucinations.
* **Whisper ASR:** An automatic speech recognition (ASR) system developed by OpenAI, trained on multilingual audio datasets, used to transcribe local language voice inputs.
* **Coqui TTS:** An open-source deep learning toolkit for Text-to-Speech synthesis, used to generate natural localized audio responses.
* **NDVI (Normalized Difference Vegetation Index):** A graphical indicator derived from satellite data (Sentinel-2, ISRO Bhuvan) that measures the greenness and vegetative density of a land parcel.
* **NDWI (Normalized Difference Water Index):** A satellite-derived index used to monitor liquid water changes in vegetation canopies, indicating crop water stress levels.
* **SHAP (SHapley Additive exPlanations):** A mathematical method based on cooperative game theory used to explain the output of machine learning models, helping farmers and officers understand why specific recommendations were generated.
* **Decision DAG (Directed Acyclic Graph):** A graphical model showing the chain of causal variables (e.g., weather anomaly -> low soil moisture -> recommendation) used for explaining AI reasoning.
* **PostGIS:** A spatial database extender for the PostgreSQL relational database, adding support for geographic objects allowing location queries in SQL.
* **pgvector:** An open-source vector similarity search extension for PostgreSQL, used in SasyaAI to store and query knowledge base RAG embeddings.
* **KEDA (Kubernetes Event-Driven Autoscaling):** A single-purpose event-driven autoscaler that scales Kubernetes workloads based on external event metrics, such as Apache Kafka message queue lag.

---

## 3. Regulatory & Compliance Terms

* **DPDP Act 2023 (Digital Personal Data Protection Act):** India's primary data privacy legislation regulating the processing of digital personal data. It enforces strict guidelines on user consent, purpose limitation, data minimization, and localization.
* **Consent Manager:** A technical system or framework that enables users (farmers) to grant, inspect, modify, or withdraw permission for the collection and processing of their digital personal data.
* **AgriStack Sandbox:** A testing environment provided by government departments allowing authorized developers to access simulated and scrubbed datasets for development and integration testing.
