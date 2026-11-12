from fastapi.testclient import TestClient
from app.main import app
PUBLIC={"/health","/api/v1/auth/login","/api/v1/auth/csrf","/api/v1/auth/demo-status","/api/v1/auth/demo-credentials","/api/v1/openapi.json","/docs","/docs/oauth2-redirect","/redoc"}
def dependency_names(route):
    found=set()
    def visit(dep):
        if dep.call: found.add(getattr(dep.call,"__name__",str(dep.call)))
        for child in dep.dependencies: visit(child)
    visit(route.dependant); return found
def test_every_non_allowlisted_route_is_authenticated():
    routes=[r for r in app.routes if hasattr(r,"path") and hasattr(r,"dependant")]
    violations=[r.path for r in routes if r.path not in PUBLIC and not ({"current_session", "ingestion_auth"} & dependency_names(r))]
    assert violations==[]
def test_health_route_exists(): assert any(route.path=="/health" for route in app.routes)
def test_mutating_authenticated_routes_require_session():
    response=TestClient(app).post("/api/v1/auth/logout")
    assert response.status_code==401
    assert response.json()["code"]=="http_401"

def test_demo_credential_fetch_is_local_opt_in_and_requires_csrf():
    from fastapi import HTTPException, Request, Response
    from app.core.config import settings
    from app.api.auth import DemoAccountIn, _local_demo_request, demo_credentials, demo_status
    previous_enabled=settings.demo_login_enabled
    previous_environment=settings.environment
    settings.demo_login_enabled=True
    settings.environment="development"
    try:
        def request_for(host):
            return Request({"type":"http","method":"POST","scheme":"http","path":"/api/v1/auth/demo-credentials","query_string":b"","headers":[(b"host",host.encode())],"client":("127.0.0.1",1234),"server":(host,80),"root_path":""})
        local=request_for("localhost")
        assert _local_demo_request(local) is True
        status=demo_status(local)
        assert status["enabled"] is True
        assert status["clinician_username"]
        assert status["admin_username"]
        try:
            demo_credentials(DemoAccountIn(account="admin"),local,Response(),None)
            assert False,"Credential retrieval must require CSRF before database access"
        except HTTPException as error:
            assert error.status_code==403
        remote=request_for("example.test")
        assert _local_demo_request(remote) is False
        try:
            demo_credentials(DemoAccountIn(account="clinician"),remote,Response(),None)
            assert False,"Remote demo credentials must be hidden"
        except HTTPException as error:
            assert error.status_code==404
        settings.environment="production"
        assert _local_demo_request(local) is False
    finally:
        settings.demo_login_enabled=previous_enabled
        settings.environment=previous_environment

def test_demo_credential_account_selection_is_allowlisted(monkeypatch):
    from pydantic import ValidationError
    from app.api.auth import DemoAccountIn, _demo_account
    from app.models.base import Role
    monkeypatch.setenv("SEED_ADMIN_USERNAME", "demo-admin")
    monkeypatch.setenv("SEED_CLINICIAN_USERNAME", "demo-clinician")
    assert _demo_account(DemoAccountIn(account="admin")) == (Role.ADMIN, "demo-admin")
    assert _demo_account(DemoAccountIn(account="clinician")) == (Role.SENIOR_CLINICIAN, "demo-clinician")
    try:
        DemoAccountIn(account="viewer")
        assert False, "Only the seeded demo administrator and clinician are allowed"
    except ValidationError:
        pass
