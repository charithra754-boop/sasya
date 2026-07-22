import pytest
import httpx
import time

GATEWAY_URL = "http://localhost:8000"

# Dynamic suffixes to prevent primary key collisions on persistent DB
unique_suffix = str(time.time_ns())[-6:]
TEST_OFFICER_NAME = f"officer_vikram_{unique_suffix}"
TEST_FARMER_AGRISTACK_ID = f"AGRI-F{unique_suffix}"
TEST_TWIN_AGRISTACK_ID = f"AGRI-T{unique_suffix}"

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
        "username": TEST_OFFICER_NAME,
        "email": f"{TEST_OFFICER_NAME}@gov.in",
        "role": "officer"
    }
    # Create User
    response_create = httpx.post(f"{GATEWAY_URL}/api/v1/users", json=user_payload)
    assert response_create.status_code == 200
    assert response_create.json()["username"] == TEST_OFFICER_NAME
    assert response_create.json()["role"] == "officer"

    # Get User
    response_get = httpx.get(f"{GATEWAY_URL}/api/v1/users/{TEST_OFFICER_NAME}")
    assert response_get.status_code == 200
    assert response_get.json()["email"] == f"{TEST_OFFICER_NAME}@gov.in"

def test_farmer_registration():
    farmer_payload = {
        "agristack_id": TEST_FARMER_AGRISTACK_ID,
        "name": "Rajesh Kumar",
        "phone": f"9876{unique_suffix}",
        "land_area_hectares": 1.5,
        "district": "Gorakhpur",
        "state": "Uttar Pradesh"
    }
    # Create Farmer
    response_create = httpx.post(f"{GATEWAY_URL}/api/v1/farmers", json=farmer_payload)
    assert response_create.status_code == 200
    assert response_create.json()["name"] == "Rajesh Kumar"

    # Get Farmer
    response_get = httpx.get(f"{GATEWAY_URL}/api/v1/farmers/{TEST_FARMER_AGRISTACK_ID}")
    assert response_get.status_code == 200
    assert response_get.json()["district"] == "Gorakhpur"

def test_digital_twin_lifecycle():
    agristack_id = TEST_TWIN_AGRISTACK_ID

    # 1. Health check
    response_health = httpx.get(f"{GATEWAY_URL}/api/v1/digital-twin/health")
    assert response_health.status_code == 200
    assert response_health.json()["status"] == "healthy"

    # Initialize twin payload
    init_payload = {
        "name": "Rajesh Twin",
        "phone": f"9988{unique_suffix}",
        "land_area": 1.8,
        "district": "Gorakhpur",
        "state": "Uttar Pradesh",
        "soil": {
            "nitrogen": 45.0,
            "phosphorus": 22.0,
            "potassium": 115.0,
            "ph": 6.8,
            "organic_carbon": 0.55,
            "water_holding_capacity": 42.0
        },
        "weather": {
            "temperature": 32.5,
            "humidity": 65.0,
            "rainfall_forecast": 12.0,
            "anomalies": None
        },
        "finance": {
            "kcc_active": True,
            "credit_score": 720,
            "outstanding_loan": 15000.0
        },
        "current_season": {
            "crop_name": "Maize",
            "sowing_date": "2026-06-15",
            "stage": "vegetative",
            "health_index": 0.78
        },
        "crop_history": [
            {
                "year": 2025,
                "season": "Rabi",
                "crop_name": "Wheat",
                "yield_kg_per_acre": 1600.0,
                "income_rupees": 32000.0
            }
        ]
    }

    # 2. Initialize Twin
    response_init = httpx.post(f"{GATEWAY_URL}/api/v1/digital-twin/{agristack_id}", json=init_payload)
    assert response_init.status_code == 201
    assert response_init.json()["version"] == 1

    # 3. Retrieve Twin
    response_get = httpx.get(f"{GATEWAY_URL}/api/v1/digital-twin/{agristack_id}")
    assert response_get.status_code == 200
    twin_data = response_get.json()
    assert twin_data["farmer"]["name"] == "Rajesh Twin"
    assert twin_data["soil"]["nitrogen"] == 45.0
    assert twin_data["current_season"]["crop_name"] == "Maize"

    # 4. Update Soil (Version increment to 2)
    soil_update = {
        "nitrogen": 60.0,
        "phosphorus": 22.0,
        "potassium": 115.0,
        "ph": 6.8,
        "organic_carbon": 0.55,
        "water_holding_capacity": 42.0
    }
    response_update = httpx.put(f"{GATEWAY_URL}/api/v1/digital-twin/{agristack_id}/soil", json=soil_update)
    assert response_update.status_code == 200
    assert response_update.json()["version"] == 2

    # 5. Fetch updated active twin
    response_get_2 = httpx.get(f"{GATEWAY_URL}/api/v1/digital-twin/{agristack_id}")
    assert response_get_2.json()["soil"]["nitrogen"] == 60.0
    assert response_get_2.json()["farmer"]["version"] == 2

    # 6. List versions
    response_versions = httpx.get(f"{GATEWAY_URL}/api/v1/digital-twin/{agristack_id}/versions")
    assert response_versions.status_code == 200
    versions_list = response_versions.json()
    assert len(versions_list) == 2
    assert versions_list[0]["version"] == 1
    assert versions_list[1]["version"] == 2

    # 7. Get Version 1 Snapshot
    response_snap = httpx.get(f"{GATEWAY_URL}/api/v1/digital-twin/{agristack_id}/versions/1")
    assert response_snap.status_code == 200
    assert response_snap.json()["soil"]["nitrogen"] == 45.0

    # 8. Rollback to Version 1 (Active version increments to 3 with Version 1 parameters)
    response_rollback = httpx.post(f"{GATEWAY_URL}/api/v1/digital-twin/{agristack_id}/rollback/1")
    assert response_rollback.status_code == 200
    assert response_rollback.json()["version"] == 3

    # 9. Verify rolled-back active state
    response_get_3 = httpx.get(f"{GATEWAY_URL}/api/v1/digital-twin/{agristack_id}")
    assert response_get_3.json()["soil"]["nitrogen"] == 45.0
    assert response_get_3.json()["farmer"]["version"] == 3

def test_knowledge_platform():
    # 1. Health Check
    response_health = httpx.get(f"{GATEWAY_URL}/api/v1/knowledge/health")
    assert response_health.status_code == 200
    assert response_health.json()["status"] == "healthy"

    # 2. Ingest documents
    doc1 = {
        "title": "PM-KISAN Scheme Guide",
        "content": "Under the PM-KISAN scheme, eligible smallholder farmers receive income support of ₹6,000 per year in three equal installments of ₹2,000 each. The benefit is directly credited to bank accounts.",
        "category": "scheme"
    }
    doc2 = {
        "title": "Urea Fertilizer Guidelines",
        "content": "Urea is the most widely used nitrogenous fertilizer. Apply maximum 100 kg/ha of Urea within 7 days of sowing to maximize corn leaf vegetative health.",
        "category": "fertilizer"
    }
    doc3 = {
        "title": "Fall Armyworm Pest Control",
        "content": "Fall Armyworm is an insect pest affecting corn and maize. To control infestation of armyworm, apply recommended neem oil dosage or chemical sprays like Spinetoram.",
        "category": "pest"
    }

    resp1 = httpx.post(f"{GATEWAY_URL}/api/v1/knowledge/ingest", json=doc1)
    assert resp1.status_code == 201
    assert resp1.json()["title"] == "PM-KISAN Scheme Guide"

    resp2 = httpx.post(f"{GATEWAY_URL}/api/v1/knowledge/ingest", json=doc2)
    assert resp2.status_code == 201
    
    resp3 = httpx.post(f"{GATEWAY_URL}/api/v1/knowledge/ingest", json=doc3)
    assert resp3.status_code == 201

    # 3. Query RAG for PM-KISAN Scheme
    query_scheme = {
        "query": "What are the benefits of the PM-KISAN subsidy scheme?",
        "category": "scheme",
        "limit": 1
    }
    resp_q1 = httpx.post(f"{GATEWAY_URL}/api/v1/knowledge/query", json=query_scheme)
    assert resp_q1.status_code == 200
    assert len(resp_q1.json()) == 1
    assert resp_q1.json()[0]["title"] == "PM-KISAN Scheme Guide"

    # 4. Query RAG for Pest Control
    query_pest = {
        "query": "How do I control the armyworm pest in my maize crop?",
        "limit": 1
    }
    resp_q2 = httpx.post(f"{GATEWAY_URL}/api/v1/knowledge/query", json=query_pest)
    assert resp_q2.status_code == 200
    assert len(resp_q2.json()) == 1
    assert resp_q2.json()[0]["title"] == "Fall Armyworm Pest Control"

    # 5. Query RAG for Urea
    query_fertilizer = {
        "query": "What is the recommended nitrogenous urea fertilizer usage?",
        "limit": 1
    }
    resp_q3 = httpx.post(f"{GATEWAY_URL}/api/v1/knowledge/query", json=query_fertilizer)
    assert resp_q3.status_code == 200
    assert len(resp_q3.json()) == 1
    assert resp_q3.json()[0]["title"] == "Urea Fertilizer Guidelines"

    # 6. Evaluate Weather Rules (Frost Risk)
    weather_input_frost = {
        "temperature": 3.2,
        "humidity": 55.0,
        "rainfall_forecast": 0.0,
        "soil_moisture": 30.0
    }
    resp_w1 = httpx.post(f"{GATEWAY_URL}/api/v1/knowledge/rules/weather", json=weather_input_frost)
    assert resp_w1.status_code == 200
    alerts = resp_w1.json()["alerts"]
    assert len(alerts) == 1
    assert alerts[0]["rule_id"] == "W-R01"
    assert alerts[0]["severity"] == "CRITICAL"

    # 7. Evaluate Weather Rules (Fungus Risk)
    weather_input_fungus = {
        "temperature": 27.5,
        "humidity": 88.0,
        "rainfall_forecast": 2.0,
        "soil_moisture": 45.0
    }
    resp_w2 = httpx.post(f"{GATEWAY_URL}/api/v1/knowledge/rules/weather", json=weather_input_fungus)
    alerts2 = resp_w2.json()["alerts"]
    assert len(alerts2) == 1
    assert alerts2[0]["rule_id"] == "W-R03"
    assert alerts2[0]["severity"] == "INFO"

    # 8. Evaluate Market Rules (MSP Hold)
    market_input_hold = {
        "crop_name": "Maize",
        "current_price": 1850.0,
        "msp_price": 2000.0,
        "price_change_7d": -1.5
    }
    resp_m1 = httpx.post(f"{GATEWAY_URL}/api/v1/knowledge/rules/market", json=market_input_hold)
    assert resp_m1.status_code == 200
    recs = resp_m1.json()["recommendations"]
    assert len(recs) == 1
    assert recs[0]["rule_id"] == "M-R01"
    assert recs[0]["action"] == "HOLD"

    # 9. Evaluate Market Rules (High Demand Sell)
    market_input_sell = {
        "crop_name": "Maize",
        "current_price": 2350.0,
        "msp_price": 2000.0,
        "price_change_7d": 11.5
    }
    resp_m2 = httpx.post(f"{GATEWAY_URL}/api/v1/knowledge/rules/market", json=market_input_sell)
    recs2 = resp_m2.json()["recommendations"]
    assert len(recs2) == 1
    assert recs2[0]["rule_id"] == "M-R03"
    assert recs2[0]["action"] == "SELL"

def test_ai_services_orchestrator():
    agristack_id = TEST_TWIN_AGRISTACK_ID

    # 1. Health check
    response_health = httpx.get(f"{GATEWAY_URL}/api/v1/orchestrator/health")
    assert response_health.status_code == 200
    assert response_health.json()["status"] == "healthy"

    # 2. Query Orchestrator for Crop Plan (Routes to Planner Agent)
    payload_plan = {
        "agristack_id": agristack_id,
        "query": "What should I plant this season and what government schemes can I get?",
        "language": "en"
    }
    resp_plan = httpx.post(f"{GATEWAY_URL}/api/v1/orchestrator/query", json=payload_plan, timeout=10.0)
    assert resp_plan.status_code == 200
    res_plan = resp_plan.json()
    assert "planner" in res_plan["agent_outputs"]
    assert "recommended_crops" in res_plan["agent_outputs"]["planner"]
    assert len(res_plan["agent_outputs"]["planner"]["recommended_crops"]) > 0
    assert "eligible_schemes" in res_plan["agent_outputs"]["planner"]

    # 3. Query Orchestrator for Pest Diagnosis (Routes to Vision Agent)
    payload_vision = {
        "agristack_id": agristack_id,
        "query": "I see worms eating my corn leaves, is it a pest infestation?",
        "language": "en"
    }
    resp_vision = httpx.post(f"{GATEWAY_URL}/api/v1/orchestrator/query", json=payload_vision, timeout=10.0)
    assert resp_vision.status_code == 200
    res_vision = resp_vision.json()
    assert "vision" in res_vision["agent_outputs"]
    assert res_vision["agent_outputs"]["vision"]["pest_name"] == "Fall Armyworm"
    assert "recommended_treatment" in res_vision["agent_outputs"]["vision"]

    # 4. Query Orchestrator for Weather & Soil Moisture (Routes to Geospatial Agent)
    payload_geo = {
        "agristack_id": agristack_id,
        "query": "Check the weather risk and soil moisture warnings",
        "language": "en"
    }
    resp_geo = httpx.post(f"{GATEWAY_URL}/api/v1/orchestrator/query", json=payload_geo, timeout=10.0)
    assert resp_geo.status_code == 200
    res_geo = resp_geo.json()
    assert "geospatial" in res_geo["agent_outputs"]
    assert "ndvi_canopy_greenness" in res_geo["agent_outputs"]["geospatial"]
    assert "alerts" in res_geo["agent_outputs"]["geospatial"]

    # 5. Query Orchestrator for Market Mandi Rates (Routes to Monitoring Agent)
    payload_market = {
        "agristack_id": agristack_id,
        "query": "Tell me the current mandi price and selling recommendation",
        "language": "en"
    }
    resp_market = httpx.post(f"{GATEWAY_URL}/api/v1/orchestrator/query", json=payload_market, timeout=10.0)
    assert resp_market.status_code == 200
    res_market = resp_market.json()
    assert "monitoring" in res_market["agent_outputs"]
    assert "current_market_price" in res_market["agent_outputs"]["monitoring"]
    assert "recommendations" in res_market["agent_outputs"]["monitoring"]

def test_decision_engine():
    # 1. Health check
    response_health = httpx.get(f"{GATEWAY_URL}/api/v1/decision-engine/health")
    assert response_health.status_code == 200
    assert response_health.json()["status"] == "healthy"

    # 2. Setup crop choices for LP optimization solver
    crop_options = [
        {
            "crop_name": "Paddy",
            "expected_yield_kg_per_hectare": 4000.0,
            "expected_price_per_kg": 22.0,      # Gross Revenue = ₹88,000/ha
            "cost_per_hectare": 30000.0,        # Profit = ₹58,000/ha
            "water_required_liters_per_hectare": 15000000.0  # High water req
        },
        {
            "crop_name": "Maize",
            "expected_yield_kg_per_hectare": 5000.0,
            "expected_price_per_kg": 20.0,      # Gross Revenue = ₹100,000/ha
            "cost_per_hectare": 40000.0,        # Profit = ₹60,000/ha
            "water_required_liters_per_hectare": 8000000.0   # Medium water req
        },
        {
            "crop_name": "Soybean",
            "expected_yield_kg_per_hectare": 2500.0,
            "expected_price_per_kg": 38.0,      # Gross Revenue = ₹95,000/ha
            "cost_per_hectare": 35000.0,        # Profit = ₹60,000/ha
            "water_required_liters_per_hectare": 6000000.0   # Low water req
        }
    ]

    opt_payload = {
        "total_land_hectares": 5.0,
        "water_budget_liters": 40000000.0,  # Limits water intensive crops
        "capital_budget_rupees": 200000.0,  # Limits high cost crops
        "crop_options": crop_options
    }

    # Execute crop allocation optimization
    resp_opt = httpx.post(f"{GATEWAY_URL}/api/v1/decision-engine/optimize", json=opt_payload)
    assert resp_opt.status_code == 200
    res_opt = resp_opt.json()
    assert res_opt["status"] in ["OPTIMAL", "FEASIBLE"]
    assert res_opt["optimal_profit_rupees"] > 0
    assert len(res_opt["allocations"]) > 0
    assert res_opt["total_land_used_hectares"] <= 5.0
    assert res_opt["total_water_used_liters"] <= 40000000.0
    assert res_opt["total_capital_used_rupees"] <= 200000.0

    # 3. Verify a proposed crop plan (Safe Case)
    verify_payload_safe = {
        "proposed_allocations": {"Soybean": 3.0, "Maize": 1.0},
        "crop_options": crop_options,
        "total_land_hectares": 5.0,
        "water_budget_liters": 40000000.0,
        "capital_budget_rupees": 200000.0
    }
    resp_v_safe = httpx.post(f"{GATEWAY_URL}/api/v1/decision-engine/verify", json=verify_payload_safe)
    assert resp_v_safe.status_code == 200
    res_v_safe = resp_v_safe.json()
    assert res_v_safe["is_safe"] is True
    assert len(res_v_safe["violations"]) == 0

    # 4. Verify a proposed crop plan (Unsafe Case: Land & Water Overuse)
    verify_payload_unsafe = {
        "proposed_allocations": {"Paddy": 4.0, "Maize": 2.0},
        "crop_options": crop_options,
        "total_land_hectares": 5.0,
        "water_budget_liters": 40000000.0,
        "capital_budget_rupees": 300000.0
    }
    resp_v_unsafe = httpx.post(f"{GATEWAY_URL}/api/v1/decision-engine/verify", json=verify_payload_unsafe)
    assert resp_v_unsafe.status_code == 200
    res_v_unsafe = resp_v_unsafe.json()
    assert res_v_unsafe["is_safe"] is False
    assert len(res_v_unsafe["violations"]) > 0
    # Confirms it caught the land limit overrun (6.0 ha > 5.0 ha) or water budget overrun
    assert any("exceeds farm limit" in v or "exceeds safe budget" in v for v in res_v_unsafe["violations"])


