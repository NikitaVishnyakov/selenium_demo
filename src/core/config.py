from dataclasses import dataclass

URLs: dict[str,str] = {
    "local": "https://www.saucedemo.com/",
    "staging": "https://staging.saucelabs.com/",
    "prod": "https://prod.saucelabs.com/"
}

@dataclass(frozen=True)
class Config:
    browser: str
    headless: bool
    remote_url: str | None
    env: str
    @property
    def base_url(self) -> str:
        return URLs[self.env]
