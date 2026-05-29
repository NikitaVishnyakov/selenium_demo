import logging
import pytest


class BaseApiTest:
    """Общий родитель для API тестов. Готовит self.petstore, self.logger."""

    @pytest.fixture(autouse=True)
    def _setup(self, petstore, request):
        self.petstore = petstore
        self.logger = logging.getLogger(request.node.name)
        yield
