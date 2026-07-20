from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import Column, Integer, String, Float, Boolean
from pydantic import BaseModel
from common.database import Base, engine, get_db
from common.logging import setup_logging
import logging

setup_logging()
logger = logging.getLogger("farmer-service")

app = FastAPI(title="SasyaAI Farmer Service", version="0.1.0")

class DbFarmer(Base):
    __tablename__ = "farmers"
    id = Column(Integer, primary_key=True, index=True)
    agristack_id = Column(String, unique=True, index=True)
    name = Column(String)
    phone = Column(String, unique=True, index=True)
    land_area_hectares = Column(Float)
    district = Column(String)
    state = Column(String)
    is_verified = Column(Boolean, default=True)

class FarmerCreate(BaseModel):
    agristack_id: str
    name: str
    phone: str
    land_area_hectares: float
    district: str
    state: str

class FarmerResponse(BaseModel):
    id: int
    agristack_id: str
    name: str
    phone: str
    land_area_hectares: float
    district: str
    state: str
    is_verified: bool

    class Config:
        from_attributes = True

@app.on_event("startup")
async def startup():
    # Automatically generate tables for development
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized for Farmer Service")

@app.get("/health")
@app.get("/api/v1/farmers/health")
def health():
    return {"status": "healthy", "service": "farmer-service"}

@app.post("/api/v1/farmers", response_model=FarmerResponse)
async def create_farmer(farmer: FarmerCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DbFarmer).where(DbFarmer.agristack_id == farmer.agristack_id))
    db_farmer = result.scalars().first()
    if db_farmer:
        raise HTTPException(status_code=400, detail="Farmer already registered with this AgriStack ID")
    
    new_farmer = DbFarmer(
        agristack_id=farmer.agristack_id,
        name=farmer.name,
        phone=farmer.phone,
        land_area_hectares=farmer.land_area_hectares,
        district=farmer.district,
        state=farmer.state
    )
    db.add(new_farmer)
    await db.commit()
    await db.refresh(new_farmer)
    logger.info(f"Farmer registered: {new_farmer.name} (AgriStack: {new_farmer.agristack_id})")
    return new_farmer

@app.get("/api/v1/farmers/{agristack_id}", response_model=FarmerResponse)
async def get_farmer(agristack_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DbFarmer).where(DbFarmer.agristack_id == agristack_id))
    db_farmer = result.scalars().first()
    if not db_farmer:
        raise HTTPException(status_code=404, detail="Farmer profile not found")
    return db_farmer
