import os
import httpx
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from common.logging import setup_logging
import logging

setup_logging()
logger = logging.getLogger("orchestrator-agent")

app = FastAPI(title="SasyaAI LLM Orchestrator Agent", version="0.1.0")

# Service endpoints configuration
DIGITAL_TWIN_SERVICE_URL = os.getenv("DIGITAL_TWIN_SERVICE_URL", "http://digital-twin:8004")
PLANNER_AGENT_URL = os.getenv("PLANNER_AGENT_URL", "http://planner-agent:8011")
VISION_AGENT_URL = os.getenv("VISION_AGENT_URL", "http://vision-agent:8012")
GEOSPATIAL_AGENT_URL = os.getenv("GEOSPATIAL_AGENT_URL", "http://geospatial-agent:8013")
MONITORING_AGENT_URL = os.getenv("MONITORING_AGENT_URL", "http://monitoring-agent:8014")

class OrchestratorQuery(BaseModel):
    agristack_id: str
    query: str
    language: Optional[str] = "en"

@app.get("/health")
@app.get("/api/v1/orchestrator/health")
def health():
    return {"status": "healthy", "service": "orchestrator-agent"}

async def fetch_digital_twin(agristack_id: str) -> Dict[str, Any]:
    url = f"{DIGITAL_TWIN_SERVICE_URL}/api/v1/digital-twin/{agristack_id}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=5.0)
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Digital twin profile not initialized")
            elif response.status_code != 200:
                raise HTTPException(status_code=502, detail="Error retrieving digital twin state")
            return response.json()
        except httpx.RequestError as exc:
            logger.error(f"Failed to reach Digital Twin service at {url}: {exc}")
            raise HTTPException(status_code=503, detail="Digital Twin service unavailable")

@app.post("/api/v1/orchestrator/query")
async def process_query(payload: OrchestratorQuery):
    logger.info(f"Orchestrator received query from {payload.agristack_id}: '{payload.query}' (Lang: {payload.language})")
    
    # 1. Fetch Dynamic Digital Twin State
    twin_state = await fetch_digital_twin(payload.agristack_id)
    
    # 2. Semantic Intent Classification
    query_lower = payload.query.lower()
    sub_agent_responses = {}
    
    async with httpx.AsyncClient() as client:
        # Route: Pest or Disease Diagnosis -> Vision Agent
        if any(w in query_lower for w in ["pest", "disease", "insect", "armyworm", "aphid", "leaf", "spot", "bug"]):
            url = f"{VISION_AGENT_URL}/api/v1/vision/diagnose"
            try:
                # In a real app we'd pass raw image, here we pass simulated metadata
                response = await client.post(url, json={"image_id": "simulated_leaf_image_101"}, timeout=5.0)
                if response.status_code == 200:
                    sub_agent_responses["vision"] = response.json()
            except httpx.RequestError:
                logger.error("Failed to connect to Vision Agent")
                sub_agent_responses["vision"] = {"error": "Vision Agent currently unavailable"}

        # Route: Sowing options, planning, crop choices, subsidies -> Planner Agent
        if any(w in query_lower for w in ["plant", "sow", "crop", "variety", "planning", "scheme", "subsidy", "benefit", "pm-kisan"]):
            url = f"{PLANNER_AGENT_URL}/api/v1/planner/plan"
            try:
                response = await client.post(url, json=twin_state, timeout=5.0)
                if response.status_code == 200:
                    sub_agent_responses["planner"] = response.json()
            except httpx.RequestError:
                logger.error("Failed to connect to Planner Agent")
                sub_agent_responses["planner"] = {"error": "Planner Agent currently unavailable"}

        # Route: Weather, rain, frost, drought, soil moisture -> Geospatial Agent
        if any(w in query_lower for w in ["weather", "rain", "temperature", "moisture", "drought", "frost", "dry-spell"]):
            url = f"{GEOSPATIAL_AGENT_URL}/api/v1/geospatial/analyze"
            try:
                response = await client.post(url, json=twin_state, timeout=5.0)
                if response.status_code == 200:
                    sub_agent_responses["geospatial"] = response.json()
            except httpx.RequestError:
                logger.error("Failed to connect to Geospatial Agent")
                sub_agent_responses["geospatial"] = {"error": "Geospatial Agent currently unavailable"}

        # Route: Prices, mandi, enam, sales, profit, selling -> Monitoring Agent
        if any(w in query_lower for w in ["price", "mandi", "market", "enam", "sell", "cost", "value"]):
            url = f"{MONITORING_AGENT_URL}/api/v1/monitoring/evaluate"
            try:
                response = await client.post(url, json=twin_state, timeout=5.0)
                if response.status_code == 200:
                    sub_agent_responses["monitoring"] = response.json()
            except httpx.RequestError:
                logger.error("Failed to connect to Monitoring Agent")
                sub_agent_responses["monitoring"] = {"error": "Monitoring Agent currently unavailable"}

    # 3. Aggregation & Synthesis
    # If no specific agent matched, default to general advice combining Planner and Weather
    if not sub_agent_responses:
        logger.info("Query matched default routing. Activating Planner and Geospatial agents.")
        async with httpx.AsyncClient() as client:
            try:
                resp_plan = await client.post(f"{PLANNER_AGENT_URL}/api/v1/planner/plan", json=twin_state, timeout=5.0)
                if resp_plan.status_code == 200:
                    sub_agent_responses["planner"] = resp_plan.json()
                resp_geo = await client.post(f"{GEOSPATIAL_AGENT_URL}/api/v1/geospatial/analyze", json=twin_state, timeout=5.0)
                if resp_geo.status_code == 200:
                    sub_agent_responses["geospatial"] = resp_geo.json()
            except httpx.RequestError:
                pass

    # 4. Construct Causal Plain-Language Synthesis (Explainability DAG representation)
    summary_parts = []
    farmer_name = twin_state["farmer"]["name"]
    
    if "planner" in sub_agent_responses and "error" not in sub_agent_responses["planner"]:
        p_data = sub_agent_responses["planner"]
        summary_parts.append(f"Planner Agent suggests planting {', '.join(p_data['recommended_crops'])}.")
        if p_data.get("eligible_schemes"):
            summary_parts.append(f"You qualify for: {', '.join(p_data['eligible_schemes'])}.")
            
    if "vision" in sub_agent_responses and "error" not in sub_agent_responses["vision"]:
        v_data = sub_agent_responses["vision"]
        summary_parts.append(f"Vision Agent diagnosed {v_data['pest_name']} (Severity: {v_data['severity_score']}/5) and recommends: {v_data['recommended_treatment']}.")
        
    if "geospatial" in sub_agent_responses and "error" not in sub_agent_responses["geospatial"]:
        g_data = sub_agent_responses["geospatial"]
        if g_data.get("alerts"):
            summary_parts.append(f"Geospatial Agent detected weather risks: {', '.join([a['title'] for a in g_data['alerts']])}.")
        else:
            summary_parts.append("Geospatial Agent reports normal weather and soil moisture indices.")
            
    if "monitoring" in sub_agent_responses and "error" not in sub_agent_responses["monitoring"]:
        m_data = sub_agent_responses["monitoring"]
        if m_data.get("recommendations"):
            summary_parts.append(f"Market Monitoring Agent advises: {', '.join([r['title'] for r in m_data['recommendations']])}.")

    final_text = f"Hello {farmer_name}. " + " ".join(summary_parts)
    
    # 5. Simulated multilingual voice output selection (Whisper/Coqui simulator)
    voice_file_path = f"/cached_voice/response_{payload.language}_{payload.agristack_id}.wav"
    
    return {
        "text_response": final_text,
        "language": payload.language,
        "voice_response_url": voice_file_path,
        "agent_outputs": sub_agent_responses,
        "confidence_score": 0.95
    }
