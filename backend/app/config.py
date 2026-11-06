"""Configuração lida de variáveis de ambiente (nenhum segredo no código)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="BSS_", extra="ignore")

    database_url: str = "sqlite:///./banco_solidario.db"
    jwt_secret: str = "somente-desenvolvimento-troque-esta-chave-em-producao"
    jwt_minutes: int = 30
    cors_origins: list[str] = ["http://localhost:4200"]
    dias_alerta_validade: int = 7
    max_tentativas_login: int = 5
    janela_bloqueio_min: int = 15
    debug: bool = False


settings = Settings()
