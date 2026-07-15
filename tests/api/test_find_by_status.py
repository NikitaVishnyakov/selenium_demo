import pytest

from tests.base_api_test import BaseApiTest


@pytest.mark.owner("nikita")
@pytest.mark.priority("P2")
@pytest.mark.api
@pytest.mark.case_id("TC-API-002")
class TestFindByStatus(BaseApiTest):
    """GET /pet/findByStatus — фильтрация по статусу."""

    @pytest.mark.parametrize("status", ["available", "pending", "sold"])
    def test_find_by_status(self, status):
        self.logger.info("GET /pet/findByStatus?status=%s", status)
        pets = self.petstore.find_by_status(status)
        assert pets, f"empty list for status={status}"
        assert all(p.get("status") == status for p in pets[:20])
