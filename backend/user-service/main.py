from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import Column, Integer, String, Boolean
from pydantic import BaseModel
from common.database import Base, engine, get_db
from common.logging import setup_logging
import logging

setup_logging()
logger = logging.getLogger("user-service")

app = FastAPI(title="SasyaAI User Service", version="0.1.0")

class DbUser(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    role = Column(String)  # "officer" or "admin"
    is_active = Column(Boolean, default=True)

class UserCreate(BaseModel):
    username: str
    email: str
    role: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True

@app.on_event("startup")
async def startup():
    # Automatically generate tables for development
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized for User Service")

@app.get("/health")
@app.get("/api/v1/users/health")
def health():
    return {"status": "healthy", "service": "user-service"}

@app.post("/api/v1/users", response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DbUser).where(DbUser.username == user.username))
    db_user = result.scalars().first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    new_user = DbUser(username=user.username, email=user.email, role=user.role)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    logger.info(f"User created: {new_user.username} with role {new_user.role}")
    return new_user

@app.get("/api/v1/users/{username}", response_model=UserResponse)
async def get_user(username: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DbUser).where(DbUser.username == username))
    db_user = result.scalars().first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
