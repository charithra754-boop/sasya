from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from common.database import Base, engine, get_db
from common.logging import setup_logging
import logging

setup_logging()
logger = logging.getLogger("digital-twin-service")

app = FastAPI(title="SasyaAI Digital Twin Service", version="0.1.0")

# ==============================================================================
# SQLAlchemy Models
# ==============================================================================

class DbFarmerTwin(Base):
    __tablename__ = "farmers_twins"
    agristack_id = Column(String, primary_key=True, index=True)
    name = Column(String)
    phone = Column(String, index=True)
    land_area = Column(Float)
    district = Column(String)
    state = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    current_version = Column(Integer, default=1)

class DbSoilRecord(Base):
    __tablename__ = "soil_records"
    agristack_id = Column(String, ForeignKey("farmers_twins.agristack_id"), primary_key=True)
    nitrogen = Column(Float)  # mg/kg
    phosphorus = Column(Float)
    potassium = Column(Float)
    ph = Column(Float)
    organic_carbon = Column(Float)
    water_holding_capacity = Column(Float)  # %
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DbWeatherRecord(Base):
    __tablename__ = "weather_records"
    agristack_id = Column(String, ForeignKey("farmers_twins.agristack_id"), primary_key=True)
    temperature = Column(Float)
    humidity = Column(Float)
    rainfall_forecast = Column(Float)  # mm
    anomalies = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DbFinancialRecord(Base):
    __tablename__ = "financial_records"
    agristack_id = Column(String, ForeignKey("farmers_twins.agristack_id"), primary_key=True)
    kcc_active = Column(Boolean, default=False)
    credit_score = Column(Integer)
    outstanding_loan = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DbCurrentSeason(Base):
    __tablename__ = "current_seasons"
    agristack_id = Column(String, ForeignKey("farmers_twins.agristack_id"), primary_key=True)
    crop_name = Column(String, nullable=True)
    sowing_date = Column(DateTime, nullable=True)
    stage = Column(String, nullable=True)  # vegetative, flowering, maturity
    health_index = Column(Float, default=1.0)  # NDVI index
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DbCropHistory(Base):
    __tablename__ = "crop_histories"
    id = Column(Integer, primary_key=True, index=True)
    agristack_id = Column(String, ForeignKey("farmers_twins.agristack_id"))
    year = Column(Integer)
    season = Column(String)  # Kharif, Rabi, Zaid
    crop_name = Column(String)
    yield_kg_per_acre = Column(Float)
    income_rupees = Column(Float)

class DbDigitalTwinVersion(Base):
    __tablename__ = "digital_twin_versions"
    id = Column(Integer, primary_key=True, index=True)
    agristack_id = Column(String, ForeignKey("farmers_twins.agristack_id"), index=True)
    version = Column(Integer)
    state = Column(JSON)  # Stores the JSON snapshot of the twin at this version
    created_at = Column(DateTime, default=datetime.utcnow)

class DbAuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    agristack_id = Column(String, index=True)
    action = Column(String)  # INITIALIZE, UPDATE_SOIL, UPDATE_WEATHER, ROLLBACK, etc.
    changed_fields = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

# ==============================================================================
# Pydantic Schemas
# ==============================================================================

class SoilUpdate(BaseModel):
    nitrogen: float
    phosphorus: float
    potassium: float
    ph: float
    organic_carbon: float
    water_holding_capacity: float

class WeatherUpdate(BaseModel):
    temperature: float
    humidity: float
    rainfall_forecast: float
    anomalies: Optional[str] = None

class FinanceUpdate(BaseModel):
    kcc_active: bool
    credit_score: int
    outstanding_loan: float

class CurrentSeasonUpdate(BaseModel):
    crop_name: str
    sowing_date: str  # YYYY-MM-DD
    stage: str
    health_index: float

class CropHistoryItem(BaseModel):
    year: int
    season: str
    crop_name: str
    yield_kg_per_acre: float
    income_rupees: float

class TwinCreate(BaseModel):
    name: str
    phone: str
    land_area: float
    district: str
    state: str
    soil: SoilUpdate
    weather: WeatherUpdate
    finance: FinanceUpdate
    current_season: Optional[CurrentSeasonUpdate] = None
    crop_history: List[CropHistoryItem] = []

# Helper function to generate complete state dictionary for version snapshotting
def construct_twin_snapshot(
    farmer: DbFarmerTwin,
    soil: DbSoilRecord,
    weather: DbWeatherRecord,
    finance: DbFinancialRecord,
    season: DbCurrentSeason,
    history: List[DbCropHistory]
) -> Dict[str, Any]:
    return {
        "farmer": {
            "agristack_id": farmer.agristack_id,
            "name": farmer.name,
            "phone": farmer.phone,
            "land_area": farmer.land_area,
            "district": farmer.district,
            "state": farmer.state,
            "version": farmer.current_version
        },
        "soil": {
            "nitrogen": soil.nitrogen,
            "phosphorus": soil.phosphorus,
            "potassium": soil.potassium,
            "ph": soil.ph,
            "organic_carbon": soil.organic_carbon,
            "water_holding_capacity": soil.water_holding_capacity
        },
        "weather": {
            "temperature": weather.temperature,
            "humidity": weather.humidity,
            "rainfall_forecast": weather.rainfall_forecast,
            "anomalies": weather.anomalies
        },
        "finance": {
            "kcc_active": finance.kcc_active,
            "credit_score": finance.credit_score,
            "outstanding_loan": finance.outstanding_loan
        },
        "current_season": {
            "crop_name": season.crop_name,
            "sowing_date": season.sowing_date.isoformat() if season.sowing_date else None,
            "stage": season.stage,
            "health_index": season.health_index
        },
        "crop_history": [
            {
                "year": h.year,
                "season": h.season,
                "crop_name": h.crop_name,
                "yield_kg_per_acre": h.yield_kg_per_acre,
                "income_rupees": h.income_rupees
            } for h in history
        ]
    }

# ==============================================================================
# Endpoint Routers
# ==============================================================================

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Digital Twin database schemas created successfully")

@app.get("/health")
@app.get("/api/v1/digital-twin/health")
def health():
    return {"status": "healthy", "service": "digital-twin-service"}

@app.post("/api/v1/digital-twin/{agristack_id}", status_code=status.HTTP_201_CREATED)
async def initialize_twin(agristack_id: str, payload: TwinCreate, db: AsyncSession = Depends(get_db)):
    # Check if exists
    result = await db.execute(select(DbFarmerTwin).where(DbFarmerTwin.agristack_id == agristack_id))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Digital twin already initialized for this AgriStack ID")

    # Create Farmer
    db_farmer = DbFarmerTwin(
        agristack_id=agristack_id,
        name=payload.name,
        phone=payload.phone,
        land_area=payload.land_area,
        district=payload.district,
        state=payload.state,
        current_version=1
    )
    db.add(db_farmer)
    await db.flush()

    # Create Soil
    db_soil = DbSoilRecord(
        agristack_id=agristack_id,
        nitrogen=payload.soil.nitrogen,
        phosphorus=payload.soil.phosphorus,
        potassium=payload.soil.potassium,
        ph=payload.soil.ph,
        organic_carbon=payload.soil.organic_carbon,
        water_holding_capacity=payload.soil.water_holding_capacity
    )
    db.add(db_soil)

    # Create Weather
    db_weather = DbWeatherRecord(
        agristack_id=agristack_id,
        temperature=payload.weather.temperature,
        humidity=payload.weather.humidity,
        rainfall_forecast=payload.weather.rainfall_forecast,
        anomalies=payload.weather.anomalies
    )
    db.add(db_weather)

    # Create Finance
    db_finance = DbFinancialRecord(
        agristack_id=agristack_id,
        kcc_active=payload.finance.kcc_active,
        credit_score=payload.finance.credit_score,
        outstanding_loan=payload.finance.outstanding_loan
    )
    db.add(db_finance)

    # Create Season
    sowing_dt = None
    if payload.current_season:
        sowing_dt = datetime.strptime(payload.current_season.sowing_date, "%Y-%m-%d")
    
    db_season = DbCurrentSeason(
        agristack_id=agristack_id,
        crop_name=payload.current_season.crop_name if payload.current_season else None,
        sowing_date=sowing_dt,
        stage=payload.current_season.stage if payload.current_season else None,
        health_index=payload.current_season.health_index if payload.current_season else 1.0
    )
    db.add(db_season)

    # Crop History items
    db_histories = []
    for h in payload.crop_history:
        db_h = DbCropHistory(
            agristack_id=agristack_id,
            year=h.year,
            season=h.season,
            crop_name=h.crop_name,
            yield_kg_per_acre=h.yield_kg_per_acre,
            income_rupees=h.income_rupees
        )
        db.add(db_h)
        db_histories.append(db_h)

    await db.flush()

    # Save Version 1 Snapshot
    snapshot = construct_twin_snapshot(db_farmer, db_soil, db_weather, db_finance, db_season, db_histories)
    db_ver = DbDigitalTwinVersion(
        agristack_id=agristack_id,
        version=1,
        state=snapshot
    )
    db.add(db_ver)

    # Write Audit Log
    db_log = DbAuditLog(
        agristack_id=agristack_id,
        action="INITIALIZE",
        changed_fields={"full_creation": True}
    )
    db.add(db_log)

    await db.commit()
    logger.info(f"Digital Twin initialized for {agristack_id}")
    return {"message": "Digital twin initialized successfully", "version": 1}

@app.get("/api/v1/digital-twin/{agristack_id}")
async def get_twin(agristack_id: str, db: AsyncSession = Depends(get_db)):
    farmer = (await db.execute(select(DbFarmerTwin).where(DbFarmerTwin.agristack_id == agristack_id))).scalars().first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Digital twin not found")

    soil = (await db.execute(select(DbSoilRecord).where(DbSoilRecord.agristack_id == agristack_id))).scalars().first()
    weather = (await db.execute(select(DbWeatherRecord).where(DbWeatherRecord.agristack_id == agristack_id))).scalars().first()
    finance = (await db.execute(select(DbFinancialRecord).where(DbFinancialRecord.agristack_id == agristack_id))).scalars().first()
    season = (await db.execute(select(DbCurrentSeason).where(DbCurrentSeason.agristack_id == agristack_id))).scalars().first()
    history = (await db.execute(select(DbCropHistory).where(DbCropHistory.agristack_id == agristack_id))).scalars().all()

    return construct_twin_snapshot(farmer, soil, weather, finance, season, history)

@app.put("/api/v1/digital-twin/{agristack_id}/soil")
async def update_soil(agristack_id: str, payload: SoilUpdate, db: AsyncSession = Depends(get_db)):
    farmer = (await db.execute(select(DbFarmerTwin).where(DbFarmerTwin.agristack_id == agristack_id))).scalars().first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Digital twin not found")
        
    soil = (await db.execute(select(DbSoilRecord).where(DbSoilRecord.agristack_id == agristack_id))).scalars().first()
    
    # Store old fields for audit log
    old_fields = {
        "nitrogen": soil.nitrogen, "phosphorus": soil.phosphorus, "potassium": soil.potassium,
        "ph": soil.ph, "organic_carbon": soil.organic_carbon, "water_holding_capacity": soil.water_holding_capacity
    }

    # Update soil parameters
    soil.nitrogen = payload.nitrogen
    soil.phosphorus = payload.phosphorus
    soil.potassium = payload.potassium
    soil.ph = payload.ph
    soil.organic_carbon = payload.organic_carbon
    soil.water_holding_capacity = payload.water_holding_capacity

    # Increment version
    farmer.current_version += 1
    
    # Fetch remainders to construct full snapshot
    weather = (await db.execute(select(DbWeatherRecord).where(DbWeatherRecord.agristack_id == agristack_id))).scalars().first()
    finance = (await db.execute(select(DbFinancialRecord).where(DbFinancialRecord.agristack_id == agristack_id))).scalars().first()
    season = (await db.execute(select(DbCurrentSeason).where(DbCurrentSeason.agristack_id == agristack_id))).scalars().first()
    history = (await db.execute(select(DbCropHistory).where(DbCropHistory.agristack_id == agristack_id))).scalars().all()

    # Save Version Snapshot
    snapshot = construct_twin_snapshot(farmer, soil, weather, finance, season, history)
    db_ver = DbDigitalTwinVersion(
        agristack_id=agristack_id,
        version=farmer.current_version,
        state=snapshot
    )
    db.add(db_ver)

    # Log changes
    db_log = DbAuditLog(
        agristack_id=agristack_id,
        action="UPDATE_SOIL",
        changed_fields={
            "old": old_fields,
            "new": payload.dict()
        }
    )
    db.add(db_log)

    await db.commit()
    logger.info(f"Soil updated for {agristack_id}. Version incremented to {farmer.current_version}")
    return {"message": "Soil record updated successfully", "version": farmer.current_version}

@app.put("/api/v1/digital-twin/{agristack_id}/weather")
async def update_weather(agristack_id: str, payload: WeatherUpdate, db: AsyncSession = Depends(get_db)):
    farmer = (await db.execute(select(DbFarmerTwin).where(DbFarmerTwin.agristack_id == agristack_id))).scalars().first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Digital twin not found")

    weather = (await db.execute(select(DbWeatherRecord).where(DbWeatherRecord.agristack_id == agristack_id))).scalars().first()
    old_fields = {
        "temperature": weather.temperature, "humidity": weather.humidity,
        "rainfall_forecast": weather.rainfall_forecast, "anomalies": weather.anomalies
    }

    weather.temperature = payload.temperature
    weather.humidity = payload.humidity
    weather.rainfall_forecast = payload.rainfall_forecast
    weather.anomalies = payload.anomalies

    farmer.current_version += 1

    soil = (await db.execute(select(DbSoilRecord).where(DbSoilRecord.agristack_id == agristack_id))).scalars().first()
    finance = (await db.execute(select(DbFinancialRecord).where(DbFinancialRecord.agristack_id == agristack_id))).scalars().first()
    season = (await db.execute(select(DbCurrentSeason).where(DbCurrentSeason.agristack_id == agristack_id))).scalars().first()
    history = (await db.execute(select(DbCropHistory).where(DbCropHistory.agristack_id == agristack_id))).scalars().all()

    snapshot = construct_twin_snapshot(farmer, soil, weather, finance, season, history)
    db_ver = DbDigitalTwinVersion(agristack_id=agristack_id, version=farmer.current_version, state=snapshot)
    db.add(db_ver)

    db_log = DbAuditLog(agristack_id=agristack_id, action="UPDATE_WEATHER", changed_fields={"old": old_fields, "new": payload.dict()})
    db.add(db_log)

    await db.commit()
    logger.info(f"Weather updated for {agristack_id}. Version incremented to {farmer.current_version}")
    return {"message": "Weather record updated successfully", "version": farmer.current_version}

@app.get("/api/v1/digital-twin/{agristack_id}/versions")
async def list_versions(agristack_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DbDigitalTwinVersion)
        .where(DbDigitalTwinVersion.agristack_id == agristack_id)
        .order_by(DbDigitalTwinVersion.version.asc())
    )
    versions = result.scalars().all()
    return [{"version": v.version, "created_at": v.created_at} for v in versions]

@app.get("/api/v1/digital-twin/{agristack_id}/versions/{version}")
async def get_version_snapshot(agristack_id: str, version: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DbDigitalTwinVersion)
        .where(DbDigitalTwinVersion.agristack_id == agristack_id, DbDigitalTwinVersion.version == version)
    )
    ver = result.scalars().first()
    if not ver:
        raise HTTPException(status_code=404, detail="Version not found")
    return ver.state

@app.post("/api/v1/digital-twin/{agristack_id}/rollback/{version}")
async def rollback_twin(agristack_id: str, version: int, db: AsyncSession = Depends(get_db)):
    # 1. Fetch the target version state
    ver_result = await db.execute(
        select(DbDigitalTwinVersion)
        .where(DbDigitalTwinVersion.agristack_id == agristack_id, DbDigitalTwinVersion.version == version)
    )
    ver = ver_result.scalars().first()
    if not ver:
        raise HTTPException(status_code=404, detail="Version not found to roll back to")
        
    state = ver.state
    
    # 2. Update active tables using target version values
    farmer = (await db.execute(select(DbFarmerTwin).where(DbFarmerTwin.agristack_id == agristack_id))).scalars().first()
    soil = (await db.execute(select(DbSoilRecord).where(DbSoilRecord.agristack_id == agristack_id))).scalars().first()
    weather = (await db.execute(select(DbWeatherRecord).where(DbWeatherRecord.agristack_id == agristack_id))).scalars().first()
    finance = (await db.execute(select(DbFinancialRecord).where(DbFinancialRecord.agristack_id == agristack_id))).scalars().first()
    season = (await db.execute(select(DbCurrentSeason).where(DbCurrentSeason.agristack_id == agristack_id))).scalars().first()

    # Update core details
    farmer.current_version += 1  # Increment version on rollback operation itself
    
    soil.nitrogen = state["soil"]["nitrogen"]
    soil.phosphorus = state["soil"]["phosphorus"]
    soil.potassium = state["soil"]["potassium"]
    soil.ph = state["soil"]["ph"]
    soil.organic_carbon = state["soil"]["organic_carbon"]
    soil.water_holding_capacity = state["soil"]["water_holding_capacity"]

    weather.temperature = state["weather"]["temperature"]
    weather.humidity = state["weather"]["humidity"]
    weather.rainfall_forecast = state["weather"]["rainfall_forecast"]
    weather.anomalies = state["weather"]["anomalies"]

    finance.kcc_active = state["finance"]["kcc_active"]
    finance.credit_score = state["finance"]["credit_score"]
    finance.outstanding_loan = state["finance"]["outstanding_loan"]

    season.crop_name = state["current_season"]["crop_name"]
    sowing_str = state["current_season"]["sowing_date"]
    season.sowing_date = datetime.fromisoformat(sowing_str) if sowing_str else None
    season.stage = state["current_season"]["stage"]
    season.health_index = state["current_season"]["health_index"]

    # Delete existing crop history for this farmer and rebuild from state
    await db.execute(select(DbCropHistory).where(DbCropHistory.agristack_id == agristack_id)) # fetch first
    # Re-fetch and clear
    hist_result = await db.execute(select(DbCropHistory).where(DbCropHistory.agristack_id == agristack_id))
    for h in hist_result.scalars().all():
        await db.delete(h)
        
    db_histories = []
    for h_item in state["crop_history"]:
        new_h = DbCropHistory(
            agristack_id=agristack_id,
            year=h_item["year"],
            season=h_item["season"],
            crop_name=h_item["crop_name"],
            yield_kg_per_acre=h_item["yield_kg_per_acre"],
            income_rupees=h_item["income_rupees"]
        )
        db.add(new_h)
        db_histories.append(new_h)

    # 3. Save new version snapshot reflecting this rollback
    new_snapshot = construct_twin_snapshot(farmer, soil, weather, finance, season, db_histories)
    new_ver_db = DbDigitalTwinVersion(
        agristack_id=agristack_id,
        version=farmer.current_version,
        state=new_snapshot
    )
    db.add(new_ver_db)

    # 4. Write audit log
    db_log = DbAuditLog(
        agristack_id=agristack_id,
        action="ROLLBACK",
        changed_fields={"rolled_back_to_version": version, "new_version": farmer.current_version}
    )
    db.add(db_log)

    await db.commit()
    logger.info(f"Digital Twin rolled back to version {version} for {agristack_id}. New version is {farmer.current_version}")
    return {"message": f"Digital Twin rolled back successfully to version {version}", "version": farmer.current_version}
