import json
import time
from pathlib import Path

import pytest
from PIL import Image, ImageChops
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains


URL = "https://kickandboom.com/dt/"
ACCEPT_COOKIES_BUTTON = (By.CSS_SELECTOR, "button.cky-btn-accept")
AGE_CONFIRM_YES_BUTTON = (By.CSS_SELECTOR, "button.age-confirmation-modal__btn--primary")
PLAY_NOW_BUTTON = (By.CSS_SELECTOR, "button.desktop-btn")
GAME_CANVAS = (By.ID, "react-unity-webgl-canvas-1")
DAILY_REWARD_CLOSE_BUTTON_COORDS = (446, 57)

BASELINES_DIR = Path(__file__).parent / "baselines"
DAILY_REWARD_BASELINE = BASELINES_DIR / "daily_reward_popup.png"


@pytest.fixture
def driver():
    options = Options()
    options.add_argument("--start-maximized")
    drv = webdriver.Chrome(options=options)
    yield drv
    drv.quit()


def open_page(driver, url: str):
    driver.get(url)


def accept_cookies(driver, timeout: int = 10):
    button = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable(ACCEPT_COOKIES_BUTTON)
    )
    button.click()


def confirm_age(driver, timeout: int = 10):
    button = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable(AGE_CONFIRM_YES_BUTTON)
    )
    button.click()


def click_play_now(driver, timeout: int = 10):
    button = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable(PLAY_NOW_BUTTON)
    )
    button.click()


def wait_for_game_canvas(driver, timeout: int = 20):
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located(GAME_CANVAS)
    )


def click_on_canvas(driver, canvas, x_offset: int = 0, y_offset: int = 0):
    ActionChains(driver) \
        .move_to_element_with_offset(canvas, x_offset, y_offset) \
        .click() \
        .perform()


def offset_from_center(canvas, x: int, y: int) -> tuple[int, int]:
    return x - canvas.size["width"] // 2, y - canvas.size["height"] // 2


def assert_canvas_matches_baseline(canvas, baseline_path: Path, tmp_path: Path, threshold: float = 0.02):
    actual_path = tmp_path / "actual.png"
    canvas.screenshot(str(actual_path))

    actual = Image.open(actual_path).convert("RGB")
    baseline = Image.open(baseline_path).convert("RGB").resize(actual.size)

    diff = ImageChops.difference(actual, baseline)
    diff_pixels = sum(1 for pixel in diff.getdata() if pixel != (0, 0, 0))
    diff_ratio = diff_pixels / (actual.width * actual.height)

    assert diff_ratio <= threshold, f"canvas differs from baseline by {diff_ratio:.2%}"


def get_game_progress(driver) -> dict:
    app_strg = driver.execute_script("return localStorage.getItem('app_strg')")
    data = json.loads(app_strg)
    progress_data = data["game"]["progress"]["PlayerData"]["Implementation"]["Data"]
    return {
        "wallet": json.loads(progress_data["WalletData"]),
        "game_progress": json.loads(progress_data["GameProgressData"]),
        "rank": json.loads(progress_data["RankData"]),
    }


def test_open_kickandboom_page(driver, tmp_path):
    open_page(driver, URL)
    assert driver.current_url == URL
    accept_cookies(driver)
    confirm_age(driver)
    click_play_now(driver)
    canvas = wait_for_game_canvas(driver)
    time.sleep(10)

    assert_canvas_matches_baseline(canvas, DAILY_REWARD_BASELINE, tmp_path)

    click_on_canvas(driver, canvas, *offset_from_center(canvas, *DAILY_REWARD_CLOSE_BUTTON_COORDS))

    progress = get_game_progress(driver)
    assert progress["wallet"]["Coins"] == 1000
    assert progress["game_progress"]["IsTutorialCompleted"] is False
