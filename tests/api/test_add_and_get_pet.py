import pytest

from src.api.models.pet import Pet
from src.utils.data_generators import make_pet
from tests.base_api_test import BaseApiTest


@pytest.mark.owner("nikita")
@pytest.mark.priority("P1")
@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.case_id("TC-API-001")
class TestAddAndGetPet(BaseApiTest):
    """POST /pet then GET /pet/{id} — round-trip + schema validation."""

    def test_add_and_get_pet(self):
        payload = make_pet()

        self.logger.info("1. POST /pet id=%s", payload["id"])
        created = self.petstore.add_pet(payload)
        assert created["id"] == payload["id"]

        self.logger.info("2. GET /pet/%s and validate schema", payload["id"])
        pet = Pet.model_validate(self.petstore.get_pet(payload["id"]))
        assert pet.name == payload["name"]
        assert pet.status == "available"
