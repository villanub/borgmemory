"""Benchmark configuration — loads from .env file and environment."""

import os
from dataclasses import dataclass
from pathlib import Path

# Load .env before reading any env vars
try:
    from dotenv import load_dotenv
    # Walk up to find .env relative to this file
    _env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(_env_path)
except ImportError:
    pass


@dataclass
class BenchConfig:
    # Borg engine
    borg_url: str = ""

    # Azure OpenAI — task execution LLM
    azure_endpoint: str = ""
    azure_api_key: str = ""
    task_model: str = "gpt-5-mini"

    # Azure OpenAI — judge LLM (can be same or different deployment)
    judge_model: str = "gpt-5-mini"

    # Database — direct connection for condition B (localhost, not docker-internal)
    database_url: str = ""

    # Benchmark defaults
    namespace: str = "azure-msp"
    condition_b_limit: int = 10

    def __post_init__(self):
        self.borg_url = os.getenv("BORG_URL", "http://localhost:8080")
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        self.azure_api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        self.task_model = os.getenv("BENCH_TASK_MODEL", "gpt-5-mini")
        self.judge_model = os.getenv("BENCH_JUDGE_MODEL", "gpt-5-mini")
        # Note: DATABASE_URL_SYNC in .env points to docker-internal hostname (borg-db).
        # Bench runs on the host, so default to localhost:5433 (the exposed port).
        self.database_url = os.getenv(
            "BENCH_DATABASE_URL",
            "postgresql://borg:borg_password@localhost:5433/borg",
        )
        self.namespace = os.getenv("BENCH_NAMESPACE", "azure-msp")


cfg = BenchConfig()
