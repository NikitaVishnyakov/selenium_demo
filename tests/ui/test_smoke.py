def test_smoke(driver, config):
    driver.get(config.base_url)
    assert "Swag Labs" in driver.title