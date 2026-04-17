"""Borg configuration via environment variables."""

from urllib.parse import urlparse

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = Field(..., description="Async PostgreSQL connection string")
    database_url_sync: str = Field(..., description="Sync PostgreSQL connection string")

    # OpenAI (OSS Borg supports standard OpenAI or Azure OpenAI)
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o-mini"

    # Optional Azure OpenAI (leave empty to use standard OpenAI)
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_embedding_endpoint: str = ""
    azure_openai_embedding_api_key: str = ""
    azure_openai_embedding_deployment: str = "text-embedding-3-small"
    azure_openai_extraction_deployment: str = "gpt-5-mini"

    # App surface
    borg_public_base_url: str = "http://localhost:8080"
    borg_enable_docs: bool = True
    borg_cors_origins: str = ""
    borg_trusted_hosts: str = ""
    borg_max_episode_content_chars: int = 20000
    borg_max_episode_metadata_bytes: int = 16000
    borg_max_episode_participants: int = 25
    borg_rate_limit_think_per_minute: int = 30
    borg_rate_limit_learn_per_minute: int = 60
    borg_rate_limit_admin_per_minute: int = 10
    borg_rate_limit_mcp_per_minute: int = 60
    borg_extraction_procedure_min_confidence: float = 0.6

    # Compiler defaults
    default_namespace: str = "default"
    hot_tier_token_budget: int = 500
    warm_tier_token_budget: int = 3000
    max_candidates: int = 20
    max_graph_hops: int = 2

    # Logging
    log_level: str = "INFO"

    @property
    def borg_cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.borg_cors_origins.split(",") if origin.strip()]

    @property
    def borg_trusted_hosts_list(self) -> list[str]:
        if self.borg_trusted_hosts:
            return [host.strip() for host in self.borg_trusted_hosts.split(",") if host.strip()]
        trusted_hosts = {"localhost", "127.0.0.1", "[::1]", "testserver"}
        parsed = urlparse(self.borg_public_base_url_value)
        if parsed.hostname:
            trusted_hosts.add(parsed.hostname)
        return sorted(trusted_hosts)

    @property
    def borg_public_base_url_value(self) -> str:
        return self.borg_public_base_url.rstrip("/")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
