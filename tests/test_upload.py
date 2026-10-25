import io
import pytest
from services.data_cleaning import DataCleaningService
from app import create_app

@pytest.fixture
def client():
    app = create_app("testing")
    with app.test_client() as client:
        yield client

def test_data_cleaning_valid_csv():
    csv_content = (
        "date,incident_type,severity,source,status,resolution_time,affected_system,description\n"
        "2026-10-01 12:00:00,Phishing,High,Email,Resolved,1.5,Exchange,Phishing email\n"
        "2026-10-02 14:00:00,Malware,Critical,Endpoint,Open,,Server,Trojan found\n"
    ).encode("utf-8")

    preview = DataCleaningService.inspect_and_preview(csv_content)
    assert preview["success"] is True
    assert preview["total_rows"] == 2
    assert preview["has_required"] is True
    assert preview["missing_required"] == []

    clean = DataCleaningService.clean_and_prepare(csv_content)
    assert clean["success"] is True
    assert clean["valid_rows_count"] == 2
    assert clean["rejected_rows_count"] == 0

def test_data_cleaning_missing_required_columns():
    # Missing 'severity' and 'source'
    bad_csv = (
        "date,incident_type,status\n"
        "2026-10-01 12:00:00,Phishing,Resolved\n"
    ).encode("utf-8")

    preview = DataCleaningService.inspect_and_preview(bad_csv)
    assert preview["success"] is True
    assert preview["has_required"] is False
    assert "severity" in preview["missing_required"]
    assert "source" in preview["missing_required"]

def test_data_cleaning_duplicate_detection():
    csv_duplicates = (
        "date,incident_type,severity,source,status\n"
        "2026-10-01 10:00:00,DDoS,High,Firewall,Resolved\n"
        "2026-10-01 10:00:00,DDoS,High,Firewall,Resolved\n"
    ).encode("utf-8")

    preview = DataCleaningService.inspect_and_preview(csv_duplicates)
    assert preview["duplicate_count"] == 1

    cleaned = DataCleaningService.clean_and_prepare(csv_duplicates, {"deduplicate": True})
    assert cleaned["valid_rows_count"] == 1
    assert "duplicate" in cleaned["reasons"][0].lower()

def test_upload_api_routes(client):
    csv_data = (
        "date,incident_type,severity,source,status\n"
        "2026-10-10 09:00:00,Brute-force,Medium,VPN,Open\n"
    ).encode("utf-8")

    # Test preview API
    data = {
        "file": (io.BytesIO(csv_data), "test_incidents.csv")
    }
    preview_res = client.post("/api/upload/preview", data=data, content_type="multipart/form-data")
    assert preview_res.status_code == 200
    assert preview_res.get_json()["has_required"] is True

    # Test import API
    data_import = {
        "file": (io.BytesIO(csv_data), "test_incidents.csv"),
        "deduplicate": "true",
        "fill_missing": "true",
        "normalize_enums": "true"
    }
    import_res = client.post("/api/upload/import", data=data_import, content_type="multipart/form-data")
    assert import_res.status_code == 200
    assert import_res.get_json()["imported_count"] == 1

def test_invalid_extension_rejection(client):
    data = {
        "file": (io.BytesIO(b"Hello world"), "malicious.exe")
    }
    res = client.post("/api/upload/preview", data=data, content_type="multipart/form-data")
    assert res.status_code == 400
    assert "Only CSV" in res.get_json()["error"]
