import os
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from common.logging import setup_logging
import logging

setup_logging()
logger = logging.getLogger("planner-agent")

app = FastAPI(title="SasyaAI Planner Agent", version="0.1.0")

KNOWLEDGE_SERVICE_URL = os.getenv("KNOWLEDGE_SERVICE_URL", "http://knowledge:8005")

class PlannerRequest(BaseModel):
    farmer: Dict[str, Any]
    soil: Dict[str, Any]
    current_season: Optional[Dict[str, Any]] = None
    crop_history: Optional[List[Dict[str, Any]]] = None

@app.get("/health")
@app.get("/api/v1/planner/health")
def health():
    return {"status": "healthy", "service": "planner-agent"}

@app.post("/api/v1/planner/plan")
async def plan_crops(payload: PlannerRequest):
    logger.info(f"Planner Agent evaluating crops for: {payload.farmer['agristack_id']}")
    
    # 1. Evaluate crop choices based on NPK/soil attributes
    recommended_crops = []
    n = payload.soil.get("nitrogen", 0.0)
    p = payload.soil.get("phosphorus", 0.0)
    ph = payload.soil.get("ph", 7.0)
    
    if ph < 6.0:
        recommended_crops.append("Paddy")
    elif ph > 7.5:
        recommended_crops.append("Cotton")
    else:
        recommended_crops.append("Wheat")
        recommended_crops.append("Maize")
        
    if n < 40.0:
        recommended_crops.append("Soybean (Legume to restore Nitrogen)")
        
    # 2. Query RAG database for subsidy schemes
    eligible_schemes = []
    async with httpx.AsyncClient() as client:
        try:
            # Query the Knowledge RAG system
            query_payload = {"query": "farmer subsidy benefit schemes", "limit": 2}
            response = await client.post(f"{KNOWLEDGE_SERVICE_URL}/api/v1/knowledge/query", json=query_payload, timeout=3.0)
            if response.status_code == 200:
                docs = response.json()
                for doc in docs:
                    eligible_schemes.append(doc["title"])
        except httpx.RequestError as exc:
            logger.error(f"Failed to query knowledge service at {KNOWLEDGE_SERVICE_URL}: {exc}")
            
    # Default fallback if RAG query returned nothing
    if not eligible_schemes:
        eligible_schemes = ["PM-KISAN Support", "PMFBY Insurance Scheme"]
        
    return {
        "agristack_id": payload.farmer["agristack_id"],
        "recommended_crops": recommended_crops,
        "eligible_schemes": eligible_schemes,
        "recommended_actions": [
            f"Given your soil pH is {ph}, focus on {', '.join(recommended_crops)}.",
            "Apply Urea or organic manure if nitrogen is low."
        ]
    }
