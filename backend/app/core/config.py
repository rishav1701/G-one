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
    cookie_secure: bool = False
    @property
    def session_secret(self) -> str:
        if self.environment != "development" and (len(self.app_secret) < 32 or self.app_secret == "change-me"):
            raise RuntimeError("APP_SECRET must be set to a non-default value of at least 32 characters")
        if self.environment == "development" and not self.app_secret:
            return "local-development-only-secret"
        return self.app_secret
settings = Settings()
