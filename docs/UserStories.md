# User Stories: SasyaAI

This document defines the complete set of User Stories for **SasyaAI**, describing the system behavior from the perspective of various stakeholders (farmers, agricultural officers, and administrators).

---

## 1. Farmer User Stories

### US-1.1: Crop Selection with Soil & Weather Constraints
* **As a** smallholder farmer (Rajesh)
* **I want to** query SasyaAI via voice in my native language for crop recommendations
* **So that** I receive an optimized crop recommendation aligned with my Soil Health Card, budget limits, and the upcoming seasonal weather forecast.
* **Actor:** Farmer
* **Pre-conditions:** Farmer has registered their profile and synced their AgriStack ID and Soil Health Card (SHC).
* **Narrative:**
  1. The farmer opens the app and taps the microphone button.
  2. The farmer asks in Hindi: *"What crop should I plant this Kharif season?"*
  3. The system captures the voice, translates it, and calls the digital twin profile.
  4. The Planner Agent fetches the soil metrics (low nitrogen) and weather models (10% lower rainfall forecast).
  5. The Google OR-Tools solver runs and eliminates high-water-consumption crops (Paddy) in favor of Maize.
  6. The system answers back via local voice audio explaining: *"Based on low soil nitrogen and a drier monsoon outlook, we recommend planting Maize instead of Paddy. Maize will optimize your yield and require 40% less water."*

### US-1.2: On-Device Pest & Disease Diagnosis
* **As a** smartphone farmer operating in a low-network area
* **I want to** photograph my crop's damaged leaves and get immediate treatment advice offline
* **So that** I can apply the correct pesticide before the infestation spreads, without needing internet connectivity.
* **Actor:** Farmer
* **Pre-conditions:** The SasyaAI app is installed with the quantised YOLOv8 pest detection weights cached on-device.
* **Narrative:**
  1. While in the field with zero network bars, the farmer notices yellow spots on cotton leaves.
  2. The farmer opens the SasyaAI app and clicks "Offline Diagnosis".
  3. The farmer captures a photo of the infected leaf.
  4. The on-device YOLOv8 classifier processes the image and identifies *Cotton Aphids* with 91% confidence.
  5. The app displays the treatment protocol (dosage: Imidacloprid at 100ml/acre) from local SQLite cache.
  6. The query and photo are queued; they automatically upload to the central digital twin store once a network connection is re-established.

### US-1.3: Voice IVR Advisory for Feature Phone Users
* **As a** marginal farmer with a basic feature phone (Lakshmi)
* **I want to** receive automated audio calls outlining weather alerts and advice in my regional language
* **So that** I can protect my crops from sudden climatic shocks without owning a smartphone.
* **Actor:** Farmer
* **Pre-conditions:** The farmer is registered in the SasyaAI database with an active mobile number and preferred language (Telugu).
* **Narrative:**
  1. The IMD data feed triggers an alert for an impending heatwave in Anantapur district.
  2. The Monitoring Agent scans active digital twins in Anantapur and flags Lakshmi's groundnut crop as high risk.
  3. The system queues a voice outbound call task via Twilio.
  4. Lakshmi's feature phone rings. She answers and hears an automated voice message in Telugu: *"Hello Lakshmi. A severe dry spell is expected starting tomorrow. Please irrigate your groundnut field today to mitigate soil moisture loss. Tap 1 to repeat this warning."*

### US-1.4: Automatic Government Scheme Matching
* **As a** marginal farmer
* **I want to** view pre-screened government schemes that match my financial and land profile
* **So that** I can apply for benefits with a single tap, without navigating complex government portals.
* **Actor:** Farmer
* **Pre-conditions:** The farmer is logged in, and their digital twin has synced land area and financial details.
* **Narrative:**
  1. The farmer navigates to the "Schemes" tab in the app.
  2. The Planner Agent fetches current central and state schemes from the RAG Knowledge Base.
  3. The constraint solver checks the farmer's landholding (< 2 ha) and category against the scheme eligibility rules.
  4. The app displays *PM-KISAN* and *PMFBY Crop Insurance* under "Recommended Schemes" with a badge: *"100% Eligible"*.
  5. The farmer taps "Apply", authorizing the system to fetch their DigiLocker credentials via AgriStack Sandbox.
  6. The pre-filled application is submitted directly to the government API.

---

## 2. Agricultural Extension Officer User Stories

### US-2.1: Village Crop Health & Water Stress Heatmaps
* **As an** agricultural extension officer (Vikram)
* **I want to** view a GIS dashboard showing NDVI indices and water stress maps of my assigned villages
* **So that** I can identify lagging areas and prioritize my field visits.
* **Actor:** Agricultural Extension Officer
* **Pre-conditions:** Officer is logged into the SasyaAI Web Portal with district boundaries configured.
* **Narrative:**
  1. The officer opens the SasyaAI Web Dashboard.
  2. The dashboard renders a map with parcel boundaries retrieved via AgriStack APIs.
  3. The Geospatial Agent computes and overlays NDVI (canopy health) and NDWI (water index) layers.
  4. The map highlights 12 plots in red indicating significant vegetative health decline over the last 14 days.
  5. The officer schedules field visits specifically targeting those 12 plots.

### US-2.2: Auditable Decision Verification
* **As an** agricultural extension officer
* **I want to** inspect the reasoning graphs of recommendations delivered to farmers
* **So that** I can verify the scientific basis of the AI advice before validating it in the field.
* **Actor:** Agricultural Extension Officer
* **Pre-conditions:** Officer is viewing a farmer's advisory log.
* **Narrative:**
  1. The officer visits Rajesh Kumar's farm. Rajesh shows a recommended plan for fertilizer application.
  2. The officer scans the barcode/ID on Rajesh's app using the officer dashboard.
  3. The system renders a Directed Acyclic Graph (DAG) illustrating the variables factored: Soil Health Card parameters, historical crop yields, and expected rainfall.
  4. The officer confirms that the AI recommendation correctly mapped to local Soil Health criteria and approves the audit log.

---

## 3. Administrator User Stories

### US-3.1: Updating Resource Budgets and Safe Usage Rules
* **As a** system administrator
* **I want to** update the NPK safety limits and regional water draw budgets via a central configuration panel
* **So that** all future recommendations immediately adhere to updated environment guidelines.
* **Actor:** System Administrator
* **Pre-conditions:** Admin has access to the admin backend panel.
* **Narrative:**
  1. The Ministry of Agriculture issues a directive lowering the allowed chemical nitrogen dosage due to soil degradation.
  2. The admin logs into the SasyaAI Config Panel.
  3. The admin changes `max_nitrogen_threshold` from 120 kg/ha to 100 kg/ha for Gorakhpur district.
  4. The admin clicks "Save and Apply".
  5. The system hot-reloads the constraint solver parameters.
  6. Within 1 minute, the OR-Tools verification engine forces all subsequent fertilizer recommendations to cap nitrogen at 100 kg/ha.
