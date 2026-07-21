import os
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from common.logging import setup_logging
import logging

setup_logging()
logger = logging.getLogger("vision-agent")

app = FastAPI(title="SasyaAI Vision Agent", version="0.1.0")

KNOWLEDGE_SERVICE_URL = os.getenv("KNOWLEDGE_SERVICE_URL", "http://knowledge:8005")

class VisionRequest(BaseModel):
    image_id: str
    metadata: Optional[Dict[str, Any]] = None

@app.get("/health")
@app.get("/api/v1/vision/health")
def health():
    return {"status": "healthy", "service": "vision-agent"}

@app.post("/api/v1/vision/diagnose")
async def diagnose_pest(payload: VisionRequest):
    logger.info(f"Vision Agent running diagnostic inference on image: {payload.image_id}")
    
    # 1. Simulate YOLOv8/EfficientNet inference classification
    diagnosed_pest = "Fall Armyworm"
    confidence = 0.92
    
    # 2. Query Knowledge Base for treatment info
    recommended_treatment = "Apply recommended neem oil or chemical sprays like Spinetoram."
    async with httpx.AsyncClient() as client:
        try:
            query_payload = {"query": f"{diagnosed_pest} treatment control method", "limit": 1}
            response = await client.post(f"{KNOWLEDGE_SERVICE_URL}/api/v1/knowledge/query", json=query_payload, timeout=3.0)
            if response.status_code == 200:
                docs = response.json()
                if docs:
                    recommended_treatment = docs[0]["content"]
        except httpx.RequestError as exc:
            logger.error(f"Failed to query knowledge service at {KNOWLEDGE_SERVICE_URL}: {exc}")
            
    return {
        "image_id": payload.image_id,
        "pest_name": diagnosed_pest,
        "confidence": confidence,
        "severity_score": 4,  # High severity
        "recommended_treatment": recommended_treatment
    }
