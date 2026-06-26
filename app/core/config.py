from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # API
    api_prefix: str = "/api"
    app_title: str = "Chat Backend API"
    app_version: str = "0.1.0"

    # Database
    db_host: str = "192.168.2.133"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = "111111"
    db_name: str = "chat"
    db_charset: str = "utf8mb4"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?charset={self.db_charset}"
        )

    # JWT
    secret_key: str = "change-me-in-production-use-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24


settings = Settings()
