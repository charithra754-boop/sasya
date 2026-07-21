import os
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from common.logging import setup_logging
import logging

setup_logging()
logger = logging.getLogger("monitoring-agent")

app = FastAPI(title="SasyaAI Monitoring Agent", version="0.1.0")

KNOWLEDGE_SERVICE_URL = os.getenv("KNOWLEDGE_SERVICE_URL", "http://knowledge:8005")

class MonitoringRequest(BaseModel):
    farmer: Dict[str, Any]
    current_season: Optional[Dict[str, Any]] = None
    finance: Optional[Dict[str, Any]] = None

@app.get("/health")
@app.get("/api/v1/monitoring/health")
def health():
    return {"status": "healthy", "service": "monitoring-agent"}

@app.post("/api/v1/monitoring/evaluate")
async def evaluate_market(payload: MonitoringRequest):
    logger.info(f"Monitoring Agent evaluating mandi trends for: {payload.farmer['agristack_id']}")
    
    # 1. Identify crop and mock price
    crop = "Maize"
    if payload.current_season and payload.current_season.get("crop_name"):
        crop = payload.current_season["crop_name"]
        
    current_price = 1850.0  # default simulated market price
    msp_price = 2000.0      # default government MSP
    
    # 2. Query market rules
    recommendations = []
    async with httpx.AsyncClient() as client:
        try:
            market_payload = {
                "crop_name": crop,
                "current_price": current_price,
                "msp_price": msp_price,
                "price_change_7d": -1.5
            }
            response = await client.post(f"{KNOWLEDGE_SERVICE_URL}/api/v1/knowledge/rules/market", json=market_payload, timeout=3.0)
            if response.status_code == 200:
                recommendations = response.json().get("recommendations", [])
        except httpx.RequestError as exc:
            logger.error(f"Failed to query knowledge market rules at {KNOWLEDGE_SERVICE_URL}: {exc}")
            
    return {
        "agristack_id": payload.farmer["agristack_id"],
        "crop_evaluated": crop,
        "current_market_price": current_price,
        "msp_price": msp_price,
        "recommendations": recommendations
    }
