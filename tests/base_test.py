import logging
import pytest

from src.core.browser_helpers import BrowserHelpers


class BaseTest(BrowserHelpers):
    """Parent for UI tests. Cooks self.driver, self.base_url, self.logger."""

    @pytest.fixture(autouse=True)
    def _setup(self, driver, base_url, request):
        self.driver = driver
        self.base_url = base_url
        self.logger = logging.getLogger(request.node.name)
        yield
