import pytest
import pandas as pd
from services.analytics import AnalyticsService
from services.threat_analysis import ThreatAnalysisService
from services.report_generator import ReportGeneratorService
from app import create_app

@pytest.fixture
def client():
    app = create_app("testing")
    with app.test_client() as client:
        yield client

def test_analytics_service_empty_df():
    empty_df = pd.DataFrame()
    summary = AnalyticsService.calculate_summary(empty_df)
    assert summary["total_incidents"] == 0
    assert summary["has_records"] is False
    assert summary["resolution_rate"] == 0.0

    trends = AnalyticsService.get_trends(empty_df)
    assert trends["dates"] == []

    heatmap = AnalyticsService.get_heatmap_matrix(empty_df)
    assert len(heatmap["days"]) == 7
    assert len(heatmap["hours"]) == 24

def test_analytics_service_calculations():
    data = {
        "incident_id": ["C1", "C2", "C3"],
        "incident_date": ["2026-10-01 10:00:00", "2026-10-02 11:00:00", "2026-10-03 12:00:00"],
        "incident_type": ["Phishing", "Ransomware", "Phishing"],
        "severity": ["Critical", "High", "Low"],
        "source": ["User Report", "SIEM", "Firewall"],
        "affected_system": ["Mail Gateway", "Finance DB", "Web Server"],
        "status": ["Resolved", "Open", "Closed"],
        "resolution_time": [2.0, None, 4.0],
        "is_demo": [1, 1, 0]
    }
    df = pd.DataFrame(data)
    summary = AnalyticsService.calculate_summary(df)
    assert summary["total_incidents"] == 3
    assert summary["critical_incidents"] == 1
    assert summary["high_incidents"] == 1
    assert summary["open_incidents"] == 1
    assert summary["resolved_incidents"] == 2
    assert summary["resolution_rate"] == 66.7
    assert summary["avg_resolution_time"] == 3.0

def test_threat_prioritization_score():
    inc_critical = {
        "severity": "Critical",
        "status": "Open",
        "affected_system": "Domain Controller",
        "incident_date": "2026-10-01 00:00:00"
    }
    score_data = ThreatAnalysisService.calculate_prioritization_score(inc_critical)
    assert score_data["score"] >= 80
    assert score_data["urgency"] == "CRITICAL PRIORITY"

    inc_low = {
        "severity": "Low",
        "status": "Resolved",
        "affected_system": "Standard Kiosk",
        "incident_date": "2026-10-24 00:00:00"
    }
    score_low = ThreatAnalysisService.calculate_prioritization_score(inc_low)
    assert score_low["score"] <= 35
    assert score_low["urgency"] == "LOW PRIORITY"

def test_pdf_report_generation():
    data = {
        "incident_id": ["C1", "C2"],
        "incident_date": ["2026-10-01 10:00:00", "2026-10-02 11:00:00"],
        "incident_type": ["Phishing", "Ransomware"],
        "severity": ["Critical", "High"],
        "source": ["SIEM", "Endpoint"],
        "affected_system": ["Mail", "DB"],
        "status": ["Resolved", "Open"],
        "resolution_time": [2.0, None]
    }
    df = pd.DataFrame(data)
    pdf_bytes = ReportGeneratorService.generate_pdf(df, title="Unit Test Audit Report")
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")
