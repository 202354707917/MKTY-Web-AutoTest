"""Read-only smoke tests for the patient portal entry."""

import logging
from urllib.parse import parse_qs, urlparse

import pytest

from pages.login_page import LoginPage
from pages.patient_entry_page import PatientEntryPage

logger = logging.getLogger(__name__)


@pytest.mark.smoke
@pytest.mark.ui
@pytest.mark.readonly
@pytest.mark.regression
def test_unauthenticated_patient_entry_redirects_to_login(driver):
    """An unauthenticated visit should render the login page."""
    patient_page = PatientEntryPage(driver)
    patient_page.open_patient_portal()
    patient_page.wait_for_document_ready()

    login_url = patient_page.wait_for_login_redirect()
    parsed_url = urlparse(login_url)
    query = parse_qs(parsed_url.query)

    assert parsed_url.path.rstrip("/") == "/login", (
        f"Expected redirect to /login, got URL: {login_url}"
    )
    assert query.get("redirect") == ["/patient"], (
        f"Expected redirect=/patient, got query: {query}"
    )

    login_page = LoginPage(driver)
    heading = login_page.wait_for_heading()
    username = login_page.wait_for_username_input()
    password = login_page.wait_for_password_input()

    assert heading.text.strip() == "登录慧医通", (
        f"Unexpected login heading: {heading.text!r}"
    )
    assert username.is_displayed(), "Username input is not visible"
    assert password.is_displayed(), "Password input is not visible"

    logger.info("Patient entry redirect and login page rendering verified.")
