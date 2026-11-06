from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from .errors import error_handlers

def install_error_handlers(app:FastAPI):
    error_handlers(app)
