import pytest
import requests

from tests.base_api_test import BaseApiTest


@pytest.mark.owner("nikita")
@pytest.mark.priority("P2")
@pytest.mark.api
@pytest.mark.case_id("TC-API-003")
class TestGetMissingPet(BaseApiTest):
    """Негативный сценарий: GET несуществующего pet → 404."""

    def test_get_missing_pet_returns_404(self):
        self.logger.info("GET /pet/0 expecting 404")
        with pytest.raises(requests.HTTPError) as exc:
            self.petstore.get_pet(0)
        assert exc.value.response.status_code == 404
