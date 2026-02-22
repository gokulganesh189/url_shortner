from pydantic_settings import BaseSettings, SettingsConfigDict
import os


# Check APP_ENV variable — default to "development" if not set
APP_ENV = os.getenv("APP_ENV", "development")

class Settings(BaseSettings):
    # MySQL
    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_database: str

    # Redis
    redis_host: str
    redis_port: int

    # App
    base_url: str
    cache_ttl_seconds: int = 3600

    model_config = SettingsConfigDict(env_file=f".env.{APP_ENV}", env_file_encoding="utf-8")

    @property
    def mysql_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )


settings = Settings()
# Show which env is loaded on startup
print(f"🌍 Running in {APP_ENV} mode — loaded .env.{APP_ENV}")