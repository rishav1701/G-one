import json, logging, uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.core.config import settings
from app.core.db import engine
from app.core.errors import error_handlers
from sqlalchemy import text
settings.session_secret
app=FastAPI(title="G One API",version="0.1.0",openapi_url="/api/v1/openapi.json")
error_handlers(app)
app.add_middleware(CORSMiddleware,allow_origins=[settings.frontend_origin],allow_credentials=True,allow_methods=["GET","POST","PUT","PATCH","DELETE"],allow_headers=["Content-Type","X-CSRF-Token","X-API-Key","Idempotency-Key","X-Request-ID"])
@app.middleware("http")
async def security_and_request_id(request:Request,call_next):
    request_id=request.headers.get("X-Request-ID") or str(uuid.uuid4()); request.state.request_id=request_id
    try: response=await call_next(request)
    except Exception:
        logging.exception(json.dumps({"request_id":request_id,"event":"unhandled_error"}))
        from fastapi.responses import JSONResponse
        response=JSONResponse(status_code=500,content={"code":"internal_error","message":"An unexpected error occurred","details":None,"request_id":request_id})
    response.headers["X-Request-ID"]=request_id
    response.headers["X-Content-Type-Options"]="nosniff"; response.headers["Referrer-Policy"]="strict-origin-when-cross-origin"; response.headers["Content-Security-Policy"]="default-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'self'"
    return response
@app.get("/health")
def health():
    with engine.connect() as connection: connection.execute(text("SELECT 1"))
    return {"status":"ok"}
app.include_router(auth_router)
