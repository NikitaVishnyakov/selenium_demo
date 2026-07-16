from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Tenant:
    username: str
    password: str


@dataclass(frozen=True)
class Config:
    host: str
    tenants: dict[str, Tenant]

    @property
    def base_url(self) -> str:
        return f"{self.host}/api/v1"

    @property
    def swagger_url(self) -> str:
        return f"{self.host}/swagger/doc.json"

    @classmethod
    def from_env(cls) -> "Config":
        host = os.environ.get("BASE_URL", "http://localhost:8080").rstrip("/")
        tenants = {
            "test1": Tenant(
                username=os.environ.get("TEST1_USER", "test1"),
                password=os.environ.get("TEST1_PASS", "test123"),
            ),
            "test2": Tenant(
                username=os.environ.get("TEST2_USER", "test2"),
                password=os.environ.get("TEST2_PASS", "test456"),
            ),
        }
        return cls(host=host, tenants=tenants)
