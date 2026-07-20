import pytest
import httpx
import time

GATEWAY_URL = "http://localhost:8000"

def test_gateway_health():
    response = httpx.get(f"{GATEWAY_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "gateway"

def test_auth_service_health():
    response = httpx.get(f"{GATEWAY_URL}/api/v1/auth/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "auth-service"

def test_user_service_health():
    response = httpx.get(f"{GATEWAY_URL}/api/v1/users/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "user-service"

def test_farmer_service_health():
    response = httpx.get(f"{GATEWAY_URL}/api/v1/farmers/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "farmer-service"

def test_auth_login():
    payload = {
        "username": "farmer123",
        "password": "password"
    }
    response = httpx.post(f"{GATEWAY_URL}/api/v1/auth/token", data=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_aadhaar_flow():
    # 1. Request OTP
    payload_req = {"aadhaar_id": "123456789012"}
    response_req = httpx.post(f"{GATEWAY_URL}/api/v1/auth/aadhaar/request", json=payload_req)
    assert response_req.status_code == 200
    assert "session_id" in response_req.json()

    # 2. Verify OTP
    payload_verify = {
        "aadhaar_id": "123456789012",
        "otp": "123456"
    }
    response_verify = httpx.post(f"{GATEWAY_URL}/api/v1/auth/aadhaar/verify", json=payload_verify)
    assert response_verify.status_code == 200
    assert "access_token" in response_verify.json()

def test_user_creation():
    user_payload = {
        "username": "officer_vikram",
        "email": "vikram@gov.in",
        "role": "officer"
    }
    # Create User
    response_create = httpx.post(f"{GATEWAY_URL}/api/v1/users", json=user_payload)
    assert response_create.status_code == 200
    assert response_create.json()["username"] == "officer_vikram"
    assert response_create.json()["role"] == "officer"

    # Get User
    response_get = httpx.get(f"{GATEWAY_URL}/api/v1/users/officer_vikram")
    assert response_get.status_code == 200
    assert response_get.json()["email"] == "vikram@gov.in"

def test_farmer_registration():
    farmer_payload = {
        "agristack_id": "AGRI-112233",
        "name": "Rajesh Kumar",
        "phone": "9876543210",
        "land_area_hectares": 1.5,
        "district": "Gorakhpur",
        "state": "Uttar Pradesh"
    }
    # Create Farmer
    response_create = httpx.post(f"{GATEWAY_URL}/api/v1/farmers", json=farmer_payload)
    assert response_create.status_code == 200
    assert response_create.json()["name"] == "Rajesh Kumar"

    # Get Farmer
    response_get = httpx.get(f"{GATEWAY_URL}/api/v1/farmers/AGRI-112233")
    assert response_get.status_code == 200
    assert response_get.json()["district"] == "Gorakhpur"
