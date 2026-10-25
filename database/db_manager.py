import os
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path is None or db_path == ":memory:":
            self.db_path = ":memory:"
            self._mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._mem_conn.row_factory = sqlite3.Row
            self._mem_conn.execute("PRAGMA foreign_keys = ON")
        else:
            self.db_path = str(Path(db_path).resolve())
            self._mem_conn = None
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)

    def get_connection(self):
        if self._mem_conn is not None:
            return self._mem_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id TEXT UNIQUE NOT NULL,
                    incident_date TEXT NOT NULL,
                    incident_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    source TEXT NOT NULL,
                    affected_system TEXT,
                    status TEXT NOT NULL,
                    resolution_time REAL,
                    description TEXT,
                    is_demo INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_date ON incidents(incident_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_type ON incidents(incident_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_severity ON incidents(severity)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status)")
            conn.commit()

    def count_incidents(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM incidents")
            return cursor.fetchone()[0]

    def seed_sample_data_if_empty(self, sample_csv_path=None):
        if self.count_incidents() > 0:
            return False
        return self.seed_sample_data(sample_csv_path)

    def seed_sample_data(self, sample_csv_path=None):
        if not sample_csv_path or not os.path.exists(sample_csv_path):
            sample_csv_path = Path(__file__).resolve().parent.parent / "data" / "sample_incidents.csv"
        
        if not os.path.exists(sample_csv_path):
            return False

        df = pd.read_csv(sample_csv_path)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for _, row in df.iterrows():
                inc_id = str(row.get("incident_id") or f"CYB-{int(datetime.now().timestamp())}")
                date_str = str(row.get("date") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                inc_type = str(row.get("incident_type") or "Other")
                sev = str(row.get("severity") or "Medium")
                source = str(row.get("source") or "SIEM")
                system = str(row.get("affected_system") or "Network")
                status = str(row.get("status") or "Open")
                res_time = row.get("resolution_time")
                res_time = float(res_time) if pd.notnull(res_time) and str(res_time).strip() != "" else None
                desc = str(row.get("description") or "Demonstration security event.")

                cursor.execute("""
                    INSERT OR IGNORE INTO incidents 
                    (incident_id, incident_date, incident_type, severity, source, affected_system, status, resolution_time, description, is_demo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (inc_id, date_str, inc_type, sev, source, system, status, res_time, desc))
            conn.commit()
        return True

    def clear_demo_data(self):
        """Removes only demonstration records without altering imported user data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM incidents WHERE is_demo = 1")
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count

    def clear_all_data(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM incidents")
            conn.commit()

    def get_incidents(self, page=1, per_page=10, search="", category=None, severity=None, status=None, start_date=None, end_date=None, sort_by="incident_date", sort_order="DESC"):
        allowed_sort = ["id", "incident_id", "incident_date", "incident_type", "severity", "source", "affected_system", "status", "resolution_time", "created_at"]
        if sort_by not in allowed_sort:
            sort_by = "incident_date"
        sort_order = "ASC" if str(sort_order).upper() == "ASC" else "DESC"

        query = "SELECT * FROM incidents WHERE 1=1"
        params = []

        if search:
            query += " AND (incident_id LIKE ? OR incident_type LIKE ? OR source LIKE ? OR affected_system LIKE ? OR description LIKE ?)"
            s = f"%{search}%"
            params.extend([s, s, s, s, s])

        if category and category != "all":
            query += " AND incident_type = ?"
            params.append(category)

        if severity and severity != "all":
            query += " AND severity = ?"
            params.append(severity)

        if status and status != "all":
            query += " AND status = ?"
            params.append(status)

        if start_date:
            query += " AND incident_date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND incident_date <= ?"
            params.append(f"{end_date} 23:59:59" if len(end_date) == 10 else end_date)

        count_query = f"SELECT COUNT(*) FROM ({query})"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]

            query += f" ORDER BY {sort_by} {sort_order} LIMIT ? OFFSET ?"
            offset = (page - 1) * per_page
            params.extend([per_page, offset])

            cursor.execute(query, params)
            rows = [dict(r) for r in cursor.fetchall()]

            return {
                "items": rows,
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": max(1, (total + per_page - 1) // per_page)
            }

    def get_incident_by_id(self, incident_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM incidents WHERE incident_id = ? OR id = ?", (incident_id, incident_id))
            row = cursor.fetchone()
            return dict(row) if row else None

    def create_incident(self, data):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            inc_id = data.get("incident_id")
            if not inc_id:
                inc_id = f"CYB-{int(datetime.now().timestamp() * 1000) % 1000000}"

            res_time = data.get("resolution_time")
            if res_time is not None and str(res_time).strip() != "":
                try:
                    res_time = float(res_time)
                except ValueError:
                    res_time = None
            else:
                res_time = None

            cursor.execute("""
                INSERT INTO incidents 
                (incident_id, incident_date, incident_type, severity, source, affected_system, status, resolution_time, description, is_demo, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                inc_id,
                data.get("incident_date") or now,
                data.get("incident_type"),
                data.get("severity"),
                data.get("source"),
                data.get("affected_system") or "Unspecified",
                data.get("status") or "Open",
                res_time,
                data.get("description") or "",
                data.get("is_demo", 0),
                now,
                now
            ))
            conn.commit()
            return self.get_incident_by_id(inc_id)

    def update_incident(self, incident_id, data):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            res_time = data.get("resolution_time")
            if res_time is not None and str(res_time).strip() != "":
                try:
                    res_time = float(res_time)
                except ValueError:
                    res_time = None
            else:
                res_time = None

            cursor.execute("""
                UPDATE incidents SET
                    incident_date = COALESCE(?, incident_date),
                    incident_type = COALESCE(?, incident_type),
                    severity = COALESCE(?, severity),
                    source = COALESCE(?, source),
                    affected_system = COALESCE(?, affected_system),
                    status = COALESCE(?, status),
                    resolution_time = ?,
                    description = COALESCE(?, description),
                    updated_at = ?
                WHERE incident_id = ? OR id = ?
            """, (
                data.get("incident_date"),
                data.get("incident_type"),
                data.get("severity"),
                data.get("source"),
                data.get("affected_system"),
                data.get("status"),
                res_time,
                data.get("description"),
                now,
                incident_id,
                incident_id
            ))
            conn.commit()
            return self.get_incident_by_id(incident_id)

    def delete_incident(self, incident_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM incidents WHERE incident_id = ? OR id = ?", (incident_id, incident_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_all_dataframe(self, filters=None):
        filters = filters or {}
        query = "SELECT * FROM incidents WHERE 1=1"
        params = []

        if filters.get("start_date"):
            query += " AND incident_date >= ?"
            params.append(filters["start_date"])

        if filters.get("end_date"):
            query += " AND incident_date <= ?"
            end_val = filters["end_date"]
            params.append(f"{end_val} 23:59:59" if len(end_val) == 10 else end_val)

        if filters.get("category") and filters["category"] != "all":
            query += " AND incident_type = ?"
            params.append(filters["category"])

        if filters.get("severity") and filters["severity"] != "all":
            query += " AND severity = ?"
            params.append(filters["severity"])

        if filters.get("status") and filters["status"] != "all":
            query += " AND status = ?"
            params.append(filters["status"])

        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)
            return df
