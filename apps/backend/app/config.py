from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str
    # Servicio Better Auth (apps/auth). AUTH_BASE_URL == BETTER_AUTH_URL del servicio (iss/aud del JWT).
    auth_base_url: str = Field(validation_alias="AUTH_BASE_URL")
    auth_jwks_url: str = Field(default="", validation_alias="AUTH_JWKS_URL")
    # "require" for Railway public proxy; "disable" for the local/internal Docker Postgres.
    db_ssl: str = Field(default="require", validation_alias="DB_SSL")
    allow_mock_auth: bool = Field(default=False, validation_alias="ALLOW_MOCK_AUTH")
    r2_account_id: str = Field(validation_alias="R2_ACCOUNT_ID")
    r2_access_key_id: str = Field(validation_alias="R2_ACCESS_KEY_ID")
    r2_secret_access_key: str = Field(validation_alias="R2_SECRET_ACCESS_KEY")
    # Empty = real Cloudflare R2. Set only for the local MinIO QA stack.
    r2_endpoint_url: str = Field(default="", validation_alias="R2_ENDPOINT_URL")
    # Solo Docker local: endpoint S3 alcanzable desde el contenedor del backend (http://s3:9090).
    r2_internal_endpoint_url: str = Field(default="", validation_alias="R2_INTERNAL_ENDPOINT_URL")
    r2_bucket: str = Field(default="iam-media", validation_alias="R2_BUCKET")
    r2_public_base: str = Field(validation_alias="R2_PUBLIC_BASE")
    media_jwt_secret: str = Field(validation_alias="MEDIA_JWT_SECRET")
    frontend_url: str
    resend_api_key: str = Field(default="", validation_alias="RESEND_API_KEY")
    certificate_verify_base_url: str = "http://localhost:8000"
    # Anti-trampa del gating de contenido (IAM-005). Solo se apagan en tests.
    enforce_realtime_heartbeat: bool = Field(default=True, validation_alias="ENFORCE_REALTIME_HEARTBEAT")
    verify_pdf_pages_server_side: bool = Field(default=True, validation_alias="VERIFY_PDF_PAGES_SERVER_SIDE")

    @model_validator(mode="after")
    def set_auth_jwks_url(self) -> "Settings":
        if not self.auth_jwks_url:
            self.auth_jwks_url = self.auth_base_url.rstrip("/") + "/api/auth/jwks"
        return self


settings = Settings()  # type: ignore[call-arg]
