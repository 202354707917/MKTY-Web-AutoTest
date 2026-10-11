"""Read-only UI checks for the patient medical record list."""

import pytest

from pages.patient_medical_record_page import PatientMedicalRecordPage


@pytest.mark.ui
@pytest.mark.readonly
@pytest.mark.regression
def test_patient_medical_records_page_reaches_read_only_state(authenticated_driver):
    """The patient medical record page shows records or an explicit empty state."""
    records_page = PatientMedicalRecordPage(authenticated_driver)
    records_page.open_medical_records()
    records_page.wait_for_route()
    records_page.wait_page_loaded()

    state = records_page.wait_for_list_state()
    assert state in {"records", "empty"}, (
        f"Unexpected medical record list state: {state!r}"
    )

    if state == "empty":
        assert records_page.is_empty_state_visible(), (
            "Medical record list reported empty but the empty state is not visible"
        )
    else:
        record = records_page.get_first_record()
        assert record is not None, (
            "Medical record list reported records but no visible record was found"
        )
        assert record["doctor"], "Medical record does not show a doctor"
        assert record["date"], "Medical record does not show a record date"
