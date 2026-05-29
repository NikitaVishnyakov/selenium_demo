import requests


class PetstoreClient:
    def __init__(self, base_url: str = "https://petstore.swagger.io/v2", timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json", "Content-Type": "application/json"})

    def add_pet(self, payload: dict) -> dict:
        r = self.session.post(f"{self.base_url}/pet", json=payload, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def get_pet(self, pet_id: int) -> dict:
        r = self.session.get(f"{self.base_url}/pet/{pet_id}", timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def delete_pet(self, pet_id: int) -> int:
        r = self.session.delete(f"{self.base_url}/pet/{pet_id}", timeout=self.timeout)
        return r.status_code

    def find_by_status(self, status: str) -> list[dict]:
        r = self.session.get(f"{self.base_url}/pet/findByStatus", params={"status": status}, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def close(self) -> None:
        self.session.close()