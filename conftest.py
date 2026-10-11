"""Shared pytest fixtures for UI automation tests."""

import logging
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Iterator
from urllib.parse import urlparse

import pytest
import allure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

PROJECT_ROOT = Path(__file__).resolve().parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
SCREENSHOTS_DIR = ARTIFACTS_DIR / "screenshots"

logger = logging.getLogger(__name__)


def _build_chrome_options(profile_dir: str) -> Options:
    """Build the isolated Chrome profile used by every WebDriver fixture."""
    options = Options()
    options.add_argument("--window-size=1440,1000")
    options.add_argument("--incognito")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-save-password-bubble")
    options.add_argument("--disable-password-generation")
    options.add_argument(
        "--disable-features="
        "PasswordLeakDetection,PasswordCheck,PasswordManagerOnboarding,"
        "AutofillServerCommunication"
    )
    options.add_experimental_option(
        "prefs",
        {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "password_manager_leak_detection": False,
        },
    )
    options.add_argument(f"--user-data-dir={profile_dir}")
    logger.info(
        "Chrome password-management protections disabled; temporary profile enabled"
    )
    return options


@pytest.fixture(scope="session")
def login_credentials() -> tuple[str, str]:
    """Read dedicated UI test credentials from process environment variables."""
    username = os.environ.get("MKTY_UI_TEST_USERNAME", "")
    password = os.environ.get("MKTY_UI_TEST_PASSWORD", "")
    missing = [
        name
        for name, value in (
            ("MKTY_UI_TEST_USERNAME", username),
            ("MKTY_UI_TEST_PASSWORD", password),
        )
        if not value.strip()
    ]
    if missing:
        raise pytest.UsageError(
            "Missing required UI test credential environment variable(s): "
            + ", ".join(missing)
        )
    return username, password


@pytest.fixture(scope="session")
def doctor_credentials() -> tuple[str, str]:
    """Read dedicated doctor UI credentials, skipping when not configured."""
    username = os.environ.get("MKTY_DOCTOR_USERNAME", "")
    password = os.environ.get("MKTY_DOCTOR_PASSWORD", "")
    if not username.strip() or not password.strip():
        pytest.skip("医生 UI 测试凭据未配置")
    return username, password


@pytest.fixture
def enable_write_test() -> None:
    """Allow data-changing UI tests only when explicitly enabled."""
    if os.environ.get("MKTY_ENABLE_WRITE_TEST", "").strip().lower() != "true":
        pytest.skip("预约写操作测试未开启")


@pytest.fixture
def booking_test_enabled() -> None:
    """Allow the booking creation and verification flow only when enabled."""
    if os.environ.get("MKTY_ENABLE_WRITE_TEST", "").strip().lower() != "true":
        pytest.skip("预约闭环写操作测试未开启")


@pytest.fixture(scope="session")
def authenticated_session_driver(
    login_credentials: tuple[str, str],
) -> Iterator[WebDriver]:
    """Start one browser, authenticate once, and keep its session for readonly tests."""
    from pages.login_page import LoginPage
    from pages.patient_entry_page import PatientEntryPage

    os.environ["SE_CACHE_PATH"] = str(PROJECT_ROOT / ".selenium-cache")

    profile_dir = tempfile.mkdtemp(prefix="mkty-selenium-session-")
    browser = None
    try:
        browser = webdriver.Chrome(options=_build_chrome_options(profile_dir))
        browser.set_page_load_timeout(30)
        patient_entry = PatientEntryPage(browser)
        patient_entry.open_patient_portal()
        patient_entry.wait_for_login_redirect()

        login_page = LoginPage(browser)
        login_page.wait_for_heading()
        login_page.enter_username(login_credentials[0])
        login_page.enter_password(login_credentials[1])
        login_page.submit()
        login_page.wait_for_patient_route()
        yield browser
    finally:
        if browser is not None:
            try:
                browser.quit()
            except Exception:
                logger.exception("Failed to quit authenticated session WebDriver")
        shutil.rmtree(profile_dir, ignore_errors=True)


@pytest.fixture
def authenticated_driver(
    request: pytest.FixtureRequest,
    authenticated_session_driver: WebDriver,
) -> Iterator[WebDriver]:
    """Expose the authenticated session and retain per-test failure evidence."""
    yield authenticated_session_driver

    setup_failed = getattr(getattr(request.node, "rep_setup", None), "failed", False)
    call_failed = getattr(getattr(request.node, "rep_call", None), "failed", False)
    if setup_failed or call_failed:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_test_name = "".join(
            char if char.isalnum() or char in "-_" else "_"
            for char in request.node.name
        )
        screenshot_path = SCREENSHOTS_DIR / f"{safe_test_name}_{timestamp}.png"
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        try:
            if authenticated_session_driver.save_screenshot(str(screenshot_path)):
                logger.error("Failure screenshot saved: %s", screenshot_path)
                try:
                    allure.attach.file(
                        str(screenshot_path),
                        name="Failure screenshot",
                        attachment_type=allure.attachment_type.PNG,
                    )
                except Exception:
                    logger.exception("Failed to attach failure screenshot to Allure")
            else:
                logger.error(
                    "WebDriver could not save screenshot: %s", screenshot_path
                )
        except Exception:
            logger.exception("Failed to capture authenticated-session screenshot")


@pytest.fixture(scope="session")
def doctor_authenticated_session_driver(
    doctor_credentials: tuple[str, str],
) -> Iterator[WebDriver]:
    """Authenticate one isolated browser session for read-only doctor tests."""
    from pages.login_page import LoginPage

    os.environ["SE_CACHE_PATH"] = str(PROJECT_ROOT / ".selenium-cache")
    profile_dir = tempfile.mkdtemp(prefix="mkty-selenium-doctor-session-")
    browser = None
    try:
        browser = webdriver.Chrome(options=_build_chrome_options(profile_dir))
        browser.set_page_load_timeout(30)
        browser.get("http://localhost:8088/login")
        login_page = LoginPage(browser)
        login_page.wait_for_heading()
        login_page.enter_username(doctor_credentials[0])
        login_page.enter_password(doctor_credentials[1])
        login_page.submit()
        WebDriverWait(browser, 10).until(
            lambda current_driver: urlparse(current_driver.current_url).path.rstrip("/")
            == "/doctor"
        )
        yield browser
    finally:
        if browser is not None:
            try:
                browser.quit()
            except Exception:
                logger.exception("Failed to quit doctor session WebDriver")
        shutil.rmtree(profile_dir, ignore_errors=True)


@pytest.fixture
def doctor_authenticated_driver(
    doctor_authenticated_session_driver: WebDriver,
) -> Iterator[WebDriver]:
    """Expose the authenticated doctor session to a read-only test."""
    yield doctor_authenticated_session_driver


@pytest.fixture
def driver(request: pytest.FixtureRequest) -> WebDriver:
    """Start a fresh Chrome session and always close it after the test."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    # Keep Selenium Manager's driver cache inside this project.
    os.environ["SE_CACHE_PATH"] = str(PROJECT_ROOT / ".selenium-cache")

    profile_dir = tempfile.mkdtemp(prefix="mkty-selenium-test-")
    browser = None
    try:
        browser = webdriver.Chrome(options=_build_chrome_options(profile_dir))
        browser.set_page_load_timeout(30)

        yield browser
    finally:
        # Capture failure evidence before closing the browser.
        setup_failed = getattr(getattr(request.node, "rep_setup", None), "failed", False)
        call_failed = getattr(getattr(request.node, "rep_call", None), "failed", False)
        if browser is not None and (setup_failed or call_failed):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_test_name = "".join(
                char if char.isalnum() or char in "-_" else "_"
                for char in request.node.name
            )
            screenshot_path = SCREENSHOTS_DIR / (
                f"{safe_test_name}_{timestamp}.png"
            )

            try:
                if browser.save_screenshot(str(screenshot_path)):
                    logger.error("Failure screenshot saved: %s", screenshot_path)
                    try:
                        allure.attach.file(
                            str(screenshot_path),
                            name="Failure screenshot",
                            attachment_type=allure.attachment_type.PNG,
                        )
                    except Exception:
                        logger.exception("Failed to attach failure screenshot to Allure")
                else:
                    logger.error("WebDriver could not save screenshot: %s", screenshot_path)
            except Exception:
                logger.exception("Failed to capture screenshot")

        if browser is not None:
            try:
                browser.quit()
            except Exception:
                logger.exception("Failed to quit WebDriver")
        shutil.rmtree(profile_dir, ignore_errors=True)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    """Expose test phase results to fixtures for failure diagnostics."""
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)
