import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app("testing")
    with app.test_client() as client:
        yield client

def test_page_routes(client):
    pages = ["/", "/dashboard", "/incidents", "/upload", "/threat-analysis", "/visualizations", "/reports", "/about", "/settings"]
    for page in pages:
        response = client.get(page)
        assert response.status_code == 200, f"Page {page} failed with status {response.status_code}"

def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["status"] == "healthy"
    assert "database_records" in json_data

def test_incident_crud_lifecycle(client):
    # 1. Create incident
    new_inc = {
        "incident_id": "TEST-CYB-001",
        "incident_date": "2026-10-25 12:00:00",
        "incident_type": "Ransomware",
        "severity": "Critical",
        "source": "Endpoint Detection",
        "affected_system": "Database Cluster",
        "status": "Open",
        "resolution_time": None,
        "description": "Test ransomware payload detected."
    }
    create_res = client.post("/api/incidents", json=new_inc)
    assert create_res.status_code == 201
    created = create_res.get_json()["incident"]
    assert created["incident_id"] == "TEST-CYB-001"

    # 2. Read single incident
    get_res = client.get(f"/api/incidents/{created['incident_id']}")
    assert get_res.status_code == 200
    assert get_res.get_json()["incident"]["severity"] == "Critical"

    # 3. Update incident
    update_res = client.put(f"/api/incidents/{created['incident_id']}", json={
        "status": "Resolved",
        "resolution_time": 4.5
    })
    assert update_res.status_code == 200
    updated = update_res.get_json()["incident"]
    assert updated["status"] == "Resolved"
    assert updated["resolution_time"] == 4.5

    # 4. Search and filter
    search_res = client.get("/api/incidents?search=Ransomware&severity=Critical")
    assert search_res.status_code == 200
    items = search_res.get_json()["data"]["items"]
    assert len(items) >= 1

    # 5. Delete incident
    del_res = client.delete(f"/api/incidents/{created['incident_id']}")
    assert del_res.status_code == 200

    # Verify deleted
    get_after = client.get(f"/api/incidents/{created['incident_id']}")
    assert get_after.status_code == 404

def test_404_handler(client):
    res = client.get("/non-existent-route")
    assert res.status_code == 404

    api_res = client.get("/api/non-existent-api")
    assert api_res.status_code == 404
    assert api_res.get_json()["success"] is False


def test_api_analytics_endpoints(client):
    endpoints = [
        "/api/analytics/summary",
        "/api/analytics/trends",
        "/api/analytics/severity",
        "/api/analytics/categories",
        "/api/analytics/sources",
        "/api/analytics/heatmap",
        "/api/threats/priorities",
        "/api/threats/deep-dive",
        "/api/ai/advisor"
    ]
    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == 200, f"Endpoint {ep} failed with status {res.status_code}"
        data = res.get_json()
        assert data["success"] is True

def test_api_reports_download(client):
    csv_res = client.get("/api/reports/export")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["Content-Type"]

    pdf_res = client.get("/api/reports/pdf?title=Custom+Security+Report")
    assert pdf_res.status_code == 200
    assert "application/pdf" in pdf_res.headers["Content-Type"]
    assert pdf_res.data.startswith(b"%PDF")

def test_api_settings_demo_actions(client):
    reset_res = client.post("/api/settings/reset-demo")
    assert reset_res.status_code == 200

    clear_res = client.post("/api/settings/clear-demo")
    assert clear_res.status_code == 200
