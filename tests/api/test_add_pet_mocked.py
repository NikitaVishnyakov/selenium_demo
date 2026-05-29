import pytest

from src.api.models.pet import Pet
from src.utils.data_generators import make_pet
from tests.base_api_test import BaseApiTest


@pytest.mark.owner("nikita")
@pytest.mark.priority("P2")
@pytest.mark.api
@pytest.mark.case_id("TC-API-004")
class TestAddPetMocked(BaseApiTest):
    """Изолируем код от сети — проверяем валидацию ответа через pydantic."""

    def test_add_pet_mocked(self, mocker):
        payload = make_pet(status="pending")
        mocker.patch.object(self.petstore, "add_pet", return_value=payload)

        self.logger.info("Call add_pet (mocked, no HTTP)")
        pet = Pet.model_validate(self.petstore.add_pet(payload))

        assert pet.status == "pending"
        self.petstore.add_pet.assert_called_once_with(payload)
