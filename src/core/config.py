from dataclasses import dataclass


# class Config:
#     def __init__(self, browser, headless, remote_url, base_url):
#         self.browser = browser
#         self.headless = headless
#         self.remote_url = remote_url
#         self.base_url = base_url
#
#     def __repr__(self):
#         return f"Config({self.browser}, {self.headless}, {self.remote_url}, {self.base_url})"
#
#     def __eq__(self, other):
#         if not isinstance(other, Config):
#             return False
#         return (self.browser, self.headless, self.remote_url, self.base_url) == ()

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
