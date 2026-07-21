import os
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from common.logging import setup_logging
import logging

setup_logging()
logger = logging.getLogger("geospatial-agent")

app = FastAPI(title="SasyaAI Geospatial Agent", version="0.1.0")

KNOWLEDGE_SERVICE_URL = os.getenv("KNOWLEDGE_SERVICE_URL", "http://knowledge:8005")

class GeospatialRequest(BaseModel):
    farmer: Dict[str, Any]
    soil: Dict[str, Any]
    weather: Optional[Dict[str, Any]] = None

@app.get("/health")
@app.get("/api/v1/geospatial/health")
def health():
    return {"status": "healthy", "service": "geospatial-agent"}

@app.post("/api/v1/geospatial/analyze")
async def analyze_conditions(payload: GeospatialRequest):
    logger.info(f"Geospatial Agent evaluating conditions for farmer twin: {payload.farmer['agristack_id']}")
    
    # 1. Fetch live metrics from payload or set default/simulated metrics
    temp = payload.weather.get("temperature", 25.0) if payload.weather else 25.0
    hum = payload.weather.get("humidity", 60.0) if payload.weather else 60.0
    rain_forecast = payload.weather.get("rainfall_forecast", 5.0) if payload.weather else 5.0
    moisture = payload.soil.get("water_holding_capacity", 35.0) # representing soil moisture proxy
    
    # 2. Query Knowledge rules service
    alerts = []
    async with httpx.AsyncClient() as client:
        try:
            weather_payload = {
                "temperature": temp,
                "humidity": hum,
                "rainfall_forecast": rain_forecast,
                "soil_moisture": moisture
            }
            response = await client.post(f"{KNOWLEDGE_SERVICE_URL}/api/v1/knowledge/rules/weather", json=weather_payload, timeout=3.0)
            if response.status_code == 200:
                alerts = response.json().get("alerts", [])
        except httpx.RequestError as exc:
            logger.error(f"Failed to query knowledge rules service at {KNOWLEDGE_SERVICE_URL}: {exc}")
            
    # Mock NDVI/NDWI satellite baseline indices
    ndvi = 0.68
    ndwi = 0.45
    
    return {
        "agristack_id": payload.farmer["agristack_id"],
        "ndvi_canopy_greenness": ndvi,
        "ndwi_canopy_water_index": ndwi,
        "alerts": alerts
    }
