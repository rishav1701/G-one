from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

def error_handlers(app):
    @app.exception_handler(StarletteHTTPException)
    async def http_error(request:Request,exc:StarletteHTTPException):
        messages={401:"Authentication required",403:"Access denied",404:"Resource not found"}
        return JSONResponse(status_code=exc.status_code,headers=exc.headers,content={"code":f"http_{exc.status_code}","message":messages.get(exc.status_code,str(exc.detail)),"details":None,"request_id":getattr(request.state,"request_id","unknown")})
    @app.exception_handler(RequestValidationError)
    async def invalid(request:Request,exc:RequestValidationError):
        return JSONResponse(status_code=422,content={"code":"validation_error","message":"Request validation failed","details":[{"field":".".join(str(x) for x in e["loc"]),"type":e["type"]} for e in exc.errors()],"request_id":getattr(request.state,"request_id","unknown")})
