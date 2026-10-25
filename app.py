import os
import io
import csv
from datetime import datetime
from flask import (
    Flask, render_template, request, jsonify, make_response, send_file, current_app
)
from werkzeug.exceptions import RequestEntityTooLarge

from config import config_by_name
from database.db_manager import DatabaseManager
from services.data_cleaning import DataCleaningService
from services.analytics import AnalyticsService
from services.threat_analysis import ThreatAnalysisService
from services.report_generator import ReportGeneratorService

def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # Initialize Database Manager
    db_manager = DatabaseManager(app.config.get("DATABASE"))
    db_manager.init_db()

    # Seed demonstration sample records on first startup if empty
    sample_csv = os.path.join(app.root_path, "data", "sample_incidents.csv")
    db_manager.seed_sample_data_if_empty(sample_csv)

    app.db_manager = db_manager

    # ------------------ ERROR HANDLERS ------------------ #
    @app.errorhandler(404)
    def page_not_found(e):
        if request.path.startswith("/api/"):
            return jsonify({"success": False, "error": "Endpoint not found"}), 404
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        if request.path.startswith("/api/"):
            return jsonify({"success": False, "error": "Internal server error occurred"}), 500
        return render_template("500.html"), 500

    @app.errorhandler(RequestEntityTooLarge)
    def file_too_large(e):
        return jsonify({"success": False, "error": "Uploaded file exceeds maximum limit of 5 MB."}), 413

    # ------------------ PAGE ROUTES ------------------ #
    @app.route("/")
    def index():
        count = app.db_manager.count_incidents()
        return render_template("index.html", incident_count=count)

    @app.route("/dashboard")
    def dashboard():
        return render_template("dashboard.html")

    @app.route("/incidents")
    def incidents():
        return render_template("incidents.html")

    @app.route("/upload")
    def upload():
        return render_template("upload.html")

    @app.route("/threat-analysis")
    def threat_analysis():
        return render_template("threat_analysis.html")

    @app.route("/visualizations")
    def visualizations():
        return render_template("visualizations.html")

    @app.route("/reports")
    def reports():
        return render_template("reports.html")

    @app.route("/about")
    def about():
        return render_template("about.html")

    @app.route("/settings")
    def settings():
        return render_template("settings.html")

    # ------------------ REST API ENDPOINTS ------------------ #
    @app.route("/api/health", methods=["GET"])
    def api_health():
        return jsonify({
            "status": "healthy",
            "service": "CyberShield AI Incident Data Analysis Engine",
            "version": "2.5.0",
            "database_records": app.db_manager.count_incidents(),
            "timestamp": datetime.now().isoformat()
        }), 200

    @app.route("/api/incidents", methods=["GET"])
    def api_get_incidents():
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        search = request.args.get("search", "", type=str)
        category = request.args.get("category", None, type=str)
        severity = request.args.get("severity", None, type=str)
        status = request.args.get("status", None, type=str)
        start_date = request.args.get("start_date", None, type=str)
        end_date = request.args.get("end_date", None, type=str)
        sort_by = request.args.get("sort_by", "incident_date", type=str)
        sort_order = request.args.get("sort_order", "DESC", type=str)

        result = app.db_manager.get_incidents(
            page=page,
            per_page=per_page,
            search=search,
            category=category,
            severity=severity,
            status=status,
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            sort_order=sort_order
        )
        return jsonify({"success": True, "data": result}), 200

    @app.route("/api/incidents", methods=["POST"])
    def api_create_incident():
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Request body must be valid JSON"}), 400

        # Validate required fields
        required = ["incident_type", "severity", "source", "status"]
        for field in required:
            if not data.get(field):
                return jsonify({"success": False, "error": f"Missing required field: '{field}'"}), 400

        try:
            created = app.db_manager.create_incident(data)
            return jsonify({"success": True, "incident": created}), 201
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/incidents/<incident_id>", methods=["GET"])
    def api_get_incident_detail(incident_id):
        inc = app.db_manager.get_incident_by_id(incident_id)
        if not inc:
            return jsonify({"success": False, "error": "Incident not found"}), 404
        return jsonify({"success": True, "incident": inc}), 200

    @app.route("/api/incidents/<incident_id>", methods=["PUT"])
    def api_update_incident(incident_id):
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Request body must be valid JSON"}), 400

        updated = app.db_manager.update_incident(incident_id, data)
        if not updated:
            return jsonify({"success": False, "error": "Incident not found"}), 404
        return jsonify({"success": True, "incident": updated}), 200

    @app.route("/api/incidents/<incident_id>", methods=["DELETE"])
    def api_delete_incident(incident_id):
        deleted = app.db_manager.delete_incident(incident_id)
        if not deleted:
            return jsonify({"success": False, "error": "Incident not found or already deleted"}), 404
        return jsonify({"success": True, "message": "Incident deleted successfully"}), 200

    @app.route("/api/upload/preview", methods=["POST"])
    def api_upload_preview():
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file uploaded in form data"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"success": False, "error": "No file selected"}), 400

        if not file.filename.lower().endswith(".csv"):
            return jsonify({"success": False, "error": "Only CSV files are allowed"}), 400

        content = file.read()
        if len(content) > app.config["MAX_CONTENT_LENGTH"]:
            return jsonify({"success": False, "error": "File size exceeds 5MB limit"}), 413

        preview_result = DataCleaningService.inspect_and_preview(content, file.filename)
        return jsonify(preview_result), 200

    @app.route("/api/upload/import", methods=["POST"])
    def api_upload_import():
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file uploaded"}), 400

        file = request.files["file"]
        content = file.read()

        options = {
            "deduplicate": request.form.get("deduplicate", "true").lower() == "true",
            "fill_missing": request.form.get("fill_missing", "true").lower() == "true",
            "normalize_enums": request.form.get("normalize_enums", "true").lower() == "true"
        }

        clean_result = DataCleaningService.clean_and_prepare(content, options)
        if not clean_result.get("success"):
            return jsonify(clean_result), 400

        records = clean_result.get("records", [])
        inserted = DataCleaningService.import_records_to_db(app.db_manager, records)

        return jsonify({
            "success": True,
            "imported_count": inserted,
            "rejected_count": clean_result.get("rejected_rows_count", 0),
            "reasons": clean_result.get("reasons", [])
        }), 200

    # Analytics Endpoints
    def _get_filtered_df():
        filters = {
            "start_date": request.args.get("start_date"),
            "end_date": request.args.get("end_date"),
            "category": request.args.get("category"),
            "severity": request.args.get("severity"),
            "status": request.args.get("status")
        }
        return app.db_manager.get_all_dataframe(filters)

    @app.route("/api/analytics/summary", methods=["GET"])
    def api_analytics_summary():
        df = _get_filtered_df()
        summary = AnalyticsService.calculate_summary(df)
        return jsonify({"success": True, "data": summary}), 200

    @app.route("/api/analytics/trends", methods=["GET"])
    def api_analytics_trends():
        df = _get_filtered_df()
        trends = AnalyticsService.get_trends(df)
        return jsonify({"success": True, "data": trends}), 200

    @app.route("/api/analytics/severity", methods=["GET"])
    def api_analytics_severity():
        df = _get_filtered_df()
        sev = AnalyticsService.get_severity_distribution(df)
        return jsonify({"success": True, "data": sev}), 200

    @app.route("/api/analytics/categories", methods=["GET"])
    def api_analytics_categories():
        df = _get_filtered_df()
        cats = AnalyticsService.get_category_distribution(df)
        return jsonify({"success": True, "data": cats}), 200

    @app.route("/api/analytics/sources", methods=["GET"])
    def api_analytics_sources():
        df = _get_filtered_df()
        sources = AnalyticsService.get_source_distribution(df)
        return jsonify({"success": True, "data": sources}), 200

    @app.route("/api/analytics/heatmap", methods=["GET"])
    def api_analytics_heatmap():
        df = _get_filtered_df()
        hm = AnalyticsService.get_heatmap_matrix(df)
        return jsonify({"success": True, "data": hm}), 200

    # Threat Analysis Endpoints
    @app.route("/api/threats/priorities", methods=["GET"])
    def api_threat_priorities():
        df = _get_filtered_df()
        priorities = ThreatAnalysisService.get_prioritized_incidents(df, limit=30)
        return jsonify({"success": True, "data": priorities}), 200

    @app.route("/api/threats/deep-dive", methods=["GET"])
    def api_threat_deep_dive():
        df = _get_filtered_df()
        deep_dive = ThreatAnalysisService.get_category_deep_dive(df)
        return jsonify({"success": True, "data": deep_dive}), 200

    @app.route("/api/ai/advisor", methods=["GET"])
    def api_ai_advisor():
        df = _get_filtered_df()
        custom_key = request.args.get("api_key") or app.config.get("GEMINI_API_KEY", "")
        insights = ThreatAnalysisService.generate_ai_insights(df, custom_key)
        return jsonify({"success": True, "data": insights}), 200

    # Export & Reports Endpoints
    @app.route("/api/reports/export", methods=["GET"])
    def api_reports_export():
        df = _get_filtered_df()
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)

        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = f"attachment; filename=cybershield_incidents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        return response

    @app.route("/api/reports/pdf", methods=["GET"])
    def api_reports_pdf():
        df = _get_filtered_df()
        title = request.args.get("title", "CyberShield AI Security Incident Analytical Report")
        pdf_bytes = ReportGeneratorService.generate_pdf(df, title=title)

        response = make_response(pdf_bytes)
        response.headers["Content-Disposition"] = f"attachment; filename=cybershield_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        response.headers["Content-Type"] = "application/pdf"
        return response

    # Settings Data Reset Endpoints
    @app.route("/api/settings/reset-demo", methods=["POST"])
    def api_reset_demo():
        sample_csv = os.path.join(app.root_path, "data", "sample_incidents.csv")
        app.db_manager.seed_sample_data(sample_csv)
        return jsonify({"success": True, "message": "Demonstration dataset refreshed successfully"}), 200

    @app.route("/api/settings/clear-demo", methods=["POST"])
    def api_clear_demo():
        deleted = app.db_manager.clear_demo_data()
        return jsonify({"success": True, "message": f"Cleared {deleted} demonstration records. User records retained."}), 200

    return app

if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV", "development") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
