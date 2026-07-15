import logging
import pytest


class BaseApiTest:
    """Parent for API tests. Cooks self.petstore, self.logger."""

    @pytest.fixture(autouse=True)
    def _setup(self, petstore, request):
        self.petstore = petstore
        self.logger = logging.getLogger(request.node.name)
        yield
