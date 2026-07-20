from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from common.security import create_access_token, decode_access_token
from common.logging import setup_logging
import logging

setup_logging()
logger = logging.getLogger("auth-service")

app = FastAPI(title="SasyaAI Auth Service", version="0.1.0")

class TokenVerify(BaseModel):
    token: str

class AadhaarOTPRequest(BaseModel):
    aadhaar_id: str

class AadhaarOTPVerify(BaseModel):
    aadhaar_id: str
    otp: str

@app.get("/health")
@app.get("/api/v1/auth/health")
def health():
    return {"status": "healthy", "service": "auth-service"}

@app.post("/api/v1/auth/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Hardcoded authentication details for dev/testing in Phase 2
    if form_data.username == "farmer123" and form_data.password == "password":
        token_data = {"sub": form_data.username, "role": "farmer", "agristack_id": "AGRI-998877"}
        token = create_access_token(data=token_data)
        logger.info(f"Token issued for user: {form_data.username}")
        return {"access_token": token, "token_type": "bearer"}
    
    logger.warning(f"Failed login attempt for user: {form_data.username}")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

@app.post("/api/v1/auth/aadhaar/request")
def request_aadhaar_otp(payload: AadhaarOTPRequest):
    # Simulated response replicating government sandbox API
    logger.info(f"Aadhaar OTP request processed for ID: {payload.aadhaar_id}")
    return {"message": "OTP sent successfully", "session_id": "sandbox_session_777"}

@app.post("/api/v1/auth/aadhaar/verify")
def verify_aadhaar_otp(payload: AadhaarOTPVerify):
    # Sandbox testing OTP matches "123456"
    if payload.otp == "123456":
        token_data = {"sub": f"aadhaar_{payload.aadhaar_id}", "role": "farmer", "agristack_id": f"AGRI-{payload.aadhaar_id[:6]}"}
        token = create_access_token(data=token_data)
        logger.info(f"Aadhaar OTP verified for ID: {payload.aadhaar_id}")
        return {"access_token": token, "token_type": "bearer"}
    
    raise HTTPException(status_code=400, detail="Invalid OTP code")

@app.post("/api/v1/auth/verify")
def verify_token(payload: TokenVerify):
    payload_data = decode_access_token(payload.token)
    if not payload_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return payload_data
