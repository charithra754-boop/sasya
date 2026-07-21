import os
import httpx
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from common.logging import setup_logging
import logging

setup_logging()
logger = logging.getLogger("gateway")

app = FastAPI(title="SasyaAI API Gateway", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8002")
FARMER_SERVICE_URL = os.getenv("FARMER_SERVICE_URL", "http://farmer-service:8003")
DIGITAL_TWIN_SERVICE_URL = os.getenv("DIGITAL_TWIN_SERVICE_URL", "http://digital-twin:8004")
KNOWLEDGE_SERVICE_URL = os.getenv("KNOWLEDGE_SERVICE_URL", "http://knowledge:8005")
ORCHESTRATOR_AGENT_URL = os.getenv("ORCHESTRATOR_AGENT_URL", "http://orchestrator-agent:8010")

SERVICE_MAP = {
    "auth": AUTH_SERVICE_URL,
    "users": USER_SERVICE_URL,
    "farmers": FARMER_SERVICE_URL,
    "digital-twin": DIGITAL_TWIN_SERVICE_URL,
    "knowledge": KNOWLEDGE_SERVICE_URL,
    "orchestrator": ORCHESTRATOR_AGENT_URL,
}

@app.get("/health", tags=["Infrastructure"])
def health_check():
    return {"status": "healthy", "service": "gateway"}

async def proxy_request(service_url: str, path: str, request: Request) -> Response:
    # Set up client
    headers = dict(request.headers)
    headers.pop("host", None)
    
    # If content-length is present, check body
    body = await request.body()
    
    query_params = str(request.query_params)
    url = f"{service_url}/{path}"
    if query_params:
        url += f"?{query_params}"
        
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body,
                timeout=10.0
            )
            
            # Exclude encoding headers that might cause decompression issues
            response_headers = dict(response.headers)
            response_headers.pop("content-encoding", None)
            response_headers.pop("transfer-encoding", None)
            
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=response_headers
            )
        except httpx.RequestError as exc:
            logger.error(f"Error proxying request to {url}: {exc}")
            raise HTTPException(status_code=502, detail="Bad Gateway")

@app.api_route("/api/v1/{service}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def route_api_root(service: str, request: Request):
    if service not in SERVICE_MAP:
        logger.warning(f"Attempted access to unregistered service root: {service}")
        raise HTTPException(status_code=404, detail="Service not found")
    
    service_url = SERVICE_MAP[service]
    routed_path = f"api/v1/{service}"
    return await proxy_request(service_url, routed_path, request)

@app.api_route("/api/v1/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def route_api(service: str, path: str, request: Request):
    if service not in SERVICE_MAP:
        logger.warning(f"Attempted access to unregistered service path: {service}/{path}")
        raise HTTPException(status_code=404, detail="Service not found")
    
    service_url = SERVICE_MAP[service]
    routed_path = f"api/v1/{service}/{path}"
    return await proxy_request(service_url, routed_path, request)
