from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    environment: str = "development"
    database_url: str = "postgresql+psycopg://gone:gone@localhost:5432/gone"
    app_secret: str = ""
    frontend_origin: str = "http://localhost:5173"
    session_idle_minutes: int = 30
    session_absolute_hours: int = 12
    login_max_failures: int = 5
    login_lock_minutes: int = 15
    observation_stale_hours: int = 24
    observation_hard_limits: dict[str, tuple[float, float]] = {
        "respiration_rate": (1, 100), "spo2": (50, 100), "systolic_bp": (30, 300),
        "pulse": (20, 300), "temperature": (25, 45),
    }
    observation_plausibility_limits: dict[str, tuple[float, float]] = {
        "respiration_rate": (9, 24), "spo2": (94, 100), "systolic_bp": (101, 219),
        "pulse": (51, 110), "temperature": (36.1, 38.0),
    }
    cookie_secure: bool = False
    @property
    def session_secret(self) -> str:
        if self.environment != "development" and (len(self.app_secret) < 32 or self.app_secret == "change-me"):
            raise RuntimeError("APP_SECRET must be set to a non-default value of at least 32 characters")
        if self.environment == "development" and not self.app_secret:
            return "local-development-only-secret"
        return self.app_secret
settings = Settings()
