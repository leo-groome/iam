from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str
    stack_project_id: str
    stack_secret_server_key: str
    stack_jwks_url: str
    r2_account_id: str
    r2_access_key_id: str
    r2_secret_access_key: str
    r2_bucket: str = "iam-media"
    r2_public_base: str
    media_jwt_secret: str
    frontend_url: str
    resend_api_key: str = ""
    certificate_verify_base_url: str = "http://localhost:8000"


settings = Settings()  # type: ignore[call-arg]
