import io
import re
import pandas as pd
import numpy as np
from datetime import datetime

VALID_SEVERITIES = {"Low", "Medium", "High", "Critical"}
VALID_STATUSES = {"Open", "In Progress", "Resolved", "Closed"}

REQUIRED_COLUMNS = ["date", "incident_type", "severity", "source", "status"]
OPTIONAL_COLUMNS = ["incident_id", "affected_system", "description", "resolution_time", "resolved_at"]

SEVERITY_MAPPING = {
    "low": "Low", "info": "Low", "1": "Low",
    "medium": "Medium", "moderate": "Medium", "warn": "Medium", "warning": "Medium", "2": "Medium",
    "high": "High", "urgent": "High", "major": "High", "3": "High",
    "critical": "Critical", "fatal": "Critical", "blocker": "Critical", "emergency": "Critical", "4": "Critical"
}

STATUS_MAPPING = {
    "open": "Open", "new": "Open", "active": "Open", "pending": "Open",
    "in progress": "In Progress", "investigating": "In Progress", "ongoing": "In Progress",
    "resolved": "Resolved", "fixed": "Resolved", "mitigated": "Resolved",
    "closed": "Closed", "completed": "Closed", "done": "Closed"
}

class DataCleaningService:
    @staticmethod
    def inspect_and_preview(csv_content_bytes, filename="uploaded.csv"):
        """Stage 1-9: Reads CSV safely, validates columns, missing values, duplicates, previews data"""
        try:
            # Safe reading
            stream = io.StringIO(csv_content_bytes.decode("utf-8", errors="replace"))
            df = pd.read_csv(stream)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse CSV file: {str(e)}"
            }

        # Normalize column names: lowercased, stripped, spaces to underscores
        raw_columns = list(df.columns)
        normalized_cols = {c: c.strip().lower().replace(" ", "_") for c in df.columns}
        df.rename(columns=normalized_cols, inplace=True)

        # Check required columns
        present_cols = set(df.columns)
        missing_required = [col for col in REQUIRED_COLUMNS if col not in present_cols]

        total_rows = len(df)
        preview_rows = df.head(5).to_dict(orient="records")

        # Duplicate detection
        duplicate_count = int(df.duplicated().sum())

        # Missing values detection
        missing_summary = {col: int(df[col].isna().sum()) for col in df.columns}

        # Check validity of severity and status
        invalid_severity_count = 0
        if "severity" in df.columns:
            invalid_severity_count = int(df["severity"].apply(
                lambda x: str(x).strip().lower() not in SEVERITY_MAPPING and str(x).strip() not in VALID_SEVERITIES
            ).sum())

        # Check dates
        invalid_date_count = 0
        if "date" in df.columns:
            def check_date(val):
                if pd.isna(val) or str(val).strip() == "":
                    return True
                try:
                    pd.to_datetime(val)
                    return False
                except Exception:
                    return True
            invalid_date_count = int(df["date"].apply(check_date).sum())

        return {
            "success": True,
            "filename": filename,
            "total_rows": total_rows,
            "columns": list(df.columns),
            "raw_columns": raw_columns,
            "missing_required": missing_required,
            "has_required": len(missing_required) == 0,
            "duplicate_count": duplicate_count,
            "missing_summary": missing_summary,
            "invalid_severity_count": invalid_severity_count,
            "invalid_date_count": invalid_date_count,
            "preview": preview_rows
        }

    @staticmethod
    def clean_and_prepare(csv_content_bytes, options=None):
        """Cleans data according to options and prepares validated records for DB insertion"""
        options = options or {}
        deduplicate = options.get("deduplicate", True)
        fill_missing = options.get("fill_missing", True)
        normalize_enums = options.get("normalize_enums", True)

        stream = io.StringIO(csv_content_bytes.decode("utf-8", errors="replace"))
        df = pd.read_csv(stream)
        df.rename(columns={c: c.strip().lower().replace(" ", "_") for c in df.columns}, inplace=True)

        initial_count = len(df)
        rejection_reasons = []

        # Check required columns
        for col in REQUIRED_COLUMNS:
            if col not in df.columns:
                return {
                    "success": False,
                    "error": f"Missing required column: '{col}'"
                }

        # Deduplicate
        if deduplicate:
            dup_mask = df.duplicated()
            dup_count = int(dup_mask.sum())
            if dup_count > 0:
                rejection_reasons.append(f"Dropped {dup_count} exact duplicate rows.")
                df = df[~dup_mask].copy()

        valid_rows = []
        rejected_rows = 0

        for idx, row in df.iterrows():
            row_dict = row.to_dict()
            row_num = idx + 2 # Header is line 1

            # Check date
            date_val = str(row_dict.get("date", "")).strip()
            if not date_val or date_val.lower() == "nan":
                rejected_rows += 1
                rejection_reasons.append(f"Row {row_num}: Missing date field.")
                continue

            try:
                parsed_date = pd.to_datetime(date_val).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                rejected_rows += 1
                rejection_reasons.append(f"Row {row_num}: Invalid date format '{date_val}'.")
                continue

            # Severity
            raw_sev = str(row_dict.get("severity", "")).strip()
            if normalize_enums and raw_sev.lower() in SEVERITY_MAPPING:
                sev = SEVERITY_MAPPING[raw_sev.lower()]
            elif raw_sev in VALID_SEVERITIES:
                sev = raw_sev
            elif fill_missing:
                sev = "Medium"
            else:
                rejected_rows += 1
                rejection_reasons.append(f"Row {row_num}: Invalid severity '{raw_sev}'.")
                continue

            # Status
            raw_status = str(row_dict.get("status", "")).strip()
            if normalize_enums and raw_status.lower() in STATUS_MAPPING:
                status = STATUS_MAPPING[raw_status.lower()]
            elif raw_status in VALID_STATUSES:
                status = raw_status
            elif fill_missing:
                status = "Open"
            else:
                rejected_rows += 1
                rejection_reasons.append(f"Row {row_num}: Invalid status '{raw_status}'.")
                continue

            # Incident Type
            raw_type = str(row_dict.get("incident_type", "")).strip()
            if not raw_type or raw_type.lower() == "nan":
                if fill_missing:
                    raw_type = "Unclassified"
                else:
                    rejected_rows += 1
                    rejection_reasons.append(f"Row {row_num}: Missing incident type.")
                    continue

            # Source
            raw_source = str(row_dict.get("source", "")).strip()
            if not raw_source or raw_source.lower() == "nan":
                raw_source = "External Monitoring" if fill_missing else "Unknown"

            # Optional fields
            affected_system = str(row_dict.get("affected_system", "")).strip()
            if not affected_system or affected_system.lower() == "nan":
                affected_system = "General Infrastructure"

            description = str(row_dict.get("description", "")).strip()
            if not description or description.lower() == "nan":
                description = f"Security event involving {raw_type} detected via {raw_source}."

            res_time_raw = row_dict.get("resolution_time")
            res_time = None
            if pd.notnull(res_time_raw) and str(res_time_raw).strip() != "":
                try:
                    res_time = float(res_time_raw)
                except ValueError:
                    res_time = None

            # Incident ID
            inc_id = str(row_dict.get("incident_id", "")).strip()
            if not inc_id or inc_id.lower() == "nan":
                inc_id = f"CYB-IMP-{int(datetime.now().timestamp() * 1000) % 1000000}-{len(valid_rows)+1}"

            valid_rows.append({
                "incident_id": inc_id,
                "incident_date": parsed_date,
                "incident_type": raw_type,
                "severity": sev,
                "source": raw_source,
                "affected_system": affected_system,
                "status": status,
                "resolution_time": res_time,
                "description": description,
                "is_demo": 0
            })

        return {
            "success": True,
            "initial_rows": initial_count,
            "valid_rows_count": len(valid_rows),
            "rejected_rows_count": rejected_rows,
            "reasons": rejection_reasons[:20],  # show top 20 rejection notes
            "total_reasons_count": len(rejection_reasons),
            "records": valid_rows
        }

    @staticmethod
    def import_records_to_db(db_manager, records):
        """Imports valid records into SQLite using a strict transaction"""
        if not records:
            return 0

        inserted = 0
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            for r in records:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO incidents 
                        (incident_id, incident_date, incident_type, severity, source, affected_system, status, resolution_time, description, is_demo)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        r["incident_id"],
                        r["incident_date"],
                        r["incident_type"],
                        r["severity"],
                        r["source"],
                        r["affected_system"],
                        r["status"],
                        r["resolution_time"],
                        r["description"],
                        r.get("is_demo", 0)
                    ))
                    inserted += 1
                except Exception as e:
                    conn.rollback()
                    raise e
            conn.commit()
        return inserted
