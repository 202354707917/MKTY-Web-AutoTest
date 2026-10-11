"""Read-only UI checks for a patient medical record detail page."""

import pytest

from pages.patient_medical_record_detail_page import PatientMedicalRecordDetailPage
from pages.patient_medical_record_page import PatientMedicalRecordPage


@pytest.mark.ui
@pytest.mark.readonly
@pytest.mark.regression
def test_patient_can_view_first_medical_record_detail(authenticated_driver):
    """A patient can open the first available medical record detail."""
    records_page = PatientMedicalRecordPage(authenticated_driver)
    records_page.open_medical_records()
    records_page.wait_for_route()
    records_page.wait_page_loaded()

    state = records_page.wait_for_list_state()
    if state == "empty":
        pytest.skip("没有可查看的病历记录")

    detail_url = records_page.get_first_record_detail_url()
    detail_page = PatientMedicalRecordDetailPage(authenticated_driver)
    detail_page.open_detail(detail_url)
    actual_url = detail_page.wait_for_route()
    detail_page.wait_page_loaded()

    assert url_path(actual_url).startswith("/patient/records/"), (
        f"Unexpected medical record detail URL: {actual_url}"
    )
    assert detail_page.get_title() == "病历详情", (
        "Medical record detail title is not visible"
    )
    assert detail_page.is_detail_visible(), (
        "Medical record detail core fields are not all visible"
    )


def url_path(url: str) -> str:
    """Return the URL path without exposing any sensitive data."""
    from urllib.parse import urlparse

    return urlparse(url).path.rstrip("/")
