import os
import numpy as np
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import Column, Integer, String, Text, text
from pgvector.sqlalchemy import Vector
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from common.database import Base, engine, get_db
from common.logging import setup_logging
import logging

setup_logging()
logger = logging.getLogger("knowledge-service")

app = FastAPI(title="SasyaAI Knowledge & RAG Service", version="0.1.0")

# ==============================================================================
# Database Model
# ==============================================================================

class DbDocument(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    content = Column(Text)
    category = Column(String(50), index=True)  # "scheme", "pest", "fertilizer", "crop"
    embedding = Column(Vector(384))  # 384-dimension vector for MiniLM embeddings

# ==============================================================================
# Embedding Generator (Deterministic Semantic Mapping for PoC / Sandbox)
# ==============================================================================

def generate_embedding(text: str) -> List[float]:
    # Dimensions: 384. Initialize with zeros.
    vec = np.zeros(384, dtype=float)
    
    # Project vocabulary terms to specific indices
    vocab_map = {
        "paddy": 0, "rice": 0,
        "wheat": 1, "grain": 1,
        "maize": 2, "corn": 2,
        "cotton": 3,
        "fertilizer": 10, "nitrogen": 11, "urea": 12, "dap": 13, "potassium": 14, "phosphorus": 15,
        "pest": 20, "disease": 21, "armyworm": 22, "aphid": 23, "blight": 24, "infestation": 25,
        "scheme": 30, "pm-kisan": 31, "subsidy": 32, "pmfby": 33, "insurance": 34, "benefit": 35,
        "weather": 40, "rain": 41, "drought": 42, "frost": 43, "heatwave": 44,
        "market": 50, "price": 51, "mandi": 52, "enam": 53, "profit": 54
    }
    
    words = text.lower().split()
    for word in words:
        # Strip simple punctuations
        cleaned = word.strip(".,;:!?()[]{}'\"")
        for kw, idx in vocab_map.items():
            if kw in cleaned:
                vec[idx] += 1.0
                
    # Normalize vector to unit length for cosine similarity
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    else:
        # Fallback to random/noise uniform vector if no keywords match to maintain valid cosine distance
        vec[383] = 1.0
        
    return vec.tolist()

# ==============================================================================
# Pydantic Schemas
# ==============================================================================

class DocumentCreate(BaseModel):
    title: str
    content: str
    category: str

class DocumentResponse(BaseModel):
    id: int
    title: str
    content: str
    category: str

    class Config:
        from_attributes = True

class RAGQuery(BaseModel):
    query: str
    category: Optional[str] = None
    limit: Optional[int] = 3

class RuleWeatherInput(BaseModel):
    temperature: float
    humidity: float
    rainfall_forecast: float
    soil_moisture: float

class RuleMarketInput(BaseModel):
    crop_name: str
    current_price: float
    msp_price: float  # Minimum Support Price
    price_change_7d: float  # Percentage change over 7 days

# ==============================================================================
# Endpoints
# ==============================================================================

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        # Enable pgvector extension inside PostgreSQL db
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Knowledge Service database schemas and vector extension initialized")

@app.get("/health")
@app.get("/api/v1/knowledge/health")
def health():
    return {"status": "healthy", "service": "knowledge-service"}

@app.post("/api/v1/knowledge/ingest", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def ingest_document(payload: DocumentCreate, db: AsyncSession = Depends(get_db)):
    vector = generate_embedding(payload.content)
    
    db_doc = DbDocument(
        title=payload.title,
        content=payload.content,
        category=payload.category,
        embedding=vector
    )
    db.add(db_doc)
    await db.commit()
    await db.refresh(db_doc)
    logger.info(f"Ingested document: {db_doc.title} (Category: {db_doc.category})")
    return db_doc

@app.post("/api/v1/knowledge/query", response_model=List[DocumentResponse])
async def query_knowledge(payload: RAGQuery, db: AsyncSession = Depends(get_db)):
    query_vector = generate_embedding(payload.query)
    
    # Cosine distance: lower distance means higher similarity
    stmt = select(DbDocument)
    
    if payload.category:
        stmt = stmt.where(DbDocument.category == payload.category)
        
    stmt = stmt.order_by(DbDocument.embedding.cosine_distance(query_vector))
    stmt = stmt.limit(payload.limit)
    
    result = await db.execute(stmt)
    documents = result.scalars().all()
    logger.info(f"Vector search retrieved {len(documents)} documents for query: '{payload.query}'")
    return documents

@app.post("/api/v1/knowledge/rules/weather")
def evaluate_weather_rules(payload: RuleWeatherInput):
    alerts = []
    
    # Rule 1: Frost Risk
    if payload.temperature <= 4.0:
        alerts.append({
            "rule_id": "W-R01",
            "severity": "CRITICAL",
            "title": "Frost Threat Alert",
            "description": "Temperature is below 4.0°C. High risk of crop cell tissue freezing. Recommended action: Apply light irrigation tonight to release heat."
        })
        
    # Rule 2: Water Stress / Dry Spell
    if payload.soil_moisture < 20.0 and payload.rainfall_forecast < 5.0:
        alerts.append({
            "rule_id": "W-R02",
            "severity": "WARNING",
            "title": "Soil Moisture Depletion",
            "description": "Soil moisture is critically low (<20%) with no incoming rain. Drought stress imminent. Recommended action: Initiate irrigation schedule."
        })
        
    # Rule 3: Humidity & Pest Spurt
    if payload.temperature >= 25.0 and payload.humidity > 80.0:
        alerts.append({
            "rule_id": "W-R03",
            "severity": "INFO",
            "title": "High Fungus Risk",
            "description": "Warm, humid conditions (Temp >=25°C, Humidity >80%) promote fungal spore germination. Check leaf under-surfaces regularly."
        })
        
    return {"alerts": alerts, "evaluated_at": datetime.utcnow().isoformat()}

@app.post("/api/v1/knowledge/rules/market")
def evaluate_market_rules(payload: RuleMarketInput):
    recommendations = []
    
    # Rule 1: Price drop below MSP (Minimum Support Price)
    if payload.current_price < payload.msp_price:
        recommendations.append({
            "rule_id": "M-R01",
            "action": "HOLD",
            "title": "Sell Warning: Price Below MSP",
            "description": f"Market price for {payload.crop_name} is below government Minimum Support Price (MSP) of ₹{payload.msp_price}/qtl. Recommended action: Store produce in local warehouse, utilize warehouse receipt loans, and delay market entry."
        })
        
    # Rule 2: Heavy price drop trend
    elif payload.price_change_7d <= -10.0:
        recommendations.append({
            "rule_id": "M-R02",
            "action": "DIVERSIFY",
            "title": "Price Drop Warning",
            "description": f"Market price for {payload.crop_name} has declined by {payload.price_change_7d}% in the last week. High mandi arrivals. Recommended action: Search alternate mandis via eNAM database or sell to processing units directly."
        })
        
    # Rule 3: High market demand
    elif payload.price_change_7d >= 10.0:
        recommendations.append({
            "rule_id": "M-R03",
            "action": "SELL",
            "title": "High Demand Opportunity",
            "description": f"Market price for {payload.crop_name} is trending up by {payload.price_change_7d}% this week. Recommended action: Harvest mature fields and sell to lock in premium margins."
        })
        
    return {"recommendations": recommendations, "evaluated_at": datetime.utcnow().isoformat()}
