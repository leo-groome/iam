from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str
    neon_auth_url: str = Field(validation_alias="NEON_AUTH_URL")
    neon_auth_jwks_url: str = Field(default="", validation_alias="NEON_AUTH_JWKS_URL")
    allow_mock_auth: bool = Field(default=False, validation_alias="ALLOW_MOCK_AUTH")
    r2_account_id: str = Field(validation_alias="R2_ACCOUNT_ID")
    r2_access_key_id: str = Field(validation_alias="R2_ACCESS_KEY_ID")
    r2_secret_access_key: str = Field(validation_alias="R2_SECRET_ACCESS_KEY")
    r2_bucket: str = Field(default="iam-media", validation_alias="R2_BUCKET")
    r2_public_base: str = Field(validation_alias="R2_PUBLIC_BASE")
    media_jwt_secret: str = Field(validation_alias="MEDIA_JWT_SECRET")
    frontend_url: str
    resend_api_key: str = Field(default="", validation_alias="RESEND_API_KEY")
    certificate_verify_base_url: str = "http://localhost:8000"

    @model_validator(mode="after")
    def set_neon_auth_jwks_url(self) -> "Settings":
        if not self.neon_auth_jwks_url:
            self.neon_auth_jwks_url = self.neon_auth_url.rstrip("/") + "/.well-known/jwks.json"
        return self


settings = Settings()  # type: ignore[call-arg]
