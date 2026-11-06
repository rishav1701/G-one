from fastapi.testclient import TestClient
from app.main import app
PUBLIC={"/health","/api/v1/auth/login","/api/v1/auth/csrf","/api/v1/openapi.json","/docs","/docs/oauth2-redirect","/redoc"}
def dependency_names(route):
    found=set()
    def visit(dep):
        if dep.call: found.add(getattr(dep.call,"__name__",str(dep.call)))
        for child in dep.dependencies: visit(child)
    visit(route.dependant); return found
def test_every_non_allowlisted_route_is_authenticated():
    routes=[r for r in app.routes if hasattr(r,"path") and hasattr(r,"dependant")]
    violations=[r.path for r in routes if r.path not in PUBLIC and "current_session" not in dependency_names(r)]
    assert violations==[]
def test_health_route_exists(): assert any(route.path=="/health" for route in app.routes)
def test_mutating_authenticated_routes_require_session():
    response=TestClient(app).post("/api/v1/auth/logout")
    assert response.status_code==401
    assert response.json()["code"]=="http_401"
