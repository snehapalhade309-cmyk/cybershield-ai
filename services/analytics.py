import pandas as pd
import numpy as np
from datetime import datetime

class AnalyticsService:
    @staticmethod
    def calculate_summary(df):
        """Calculates KPI cards from incident dataframe"""
        if df.empty:
            return {
                "total_incidents": 0,
                "critical_incidents": 0,
                "high_incidents": 0,
                "medium_incidents": 0,
                "low_incidents": 0,
                "open_incidents": 0,
                "in_progress_incidents": 0,
                "resolved_incidents": 0,
                "closed_incidents": 0,
                "resolution_rate": 0.0,
                "avg_resolution_time": 0.0,
                "is_demo_count": 0,
                "has_records": False
            }

        total = len(df)
        sev_counts = df["severity"].value_counts().to_dict()
        status_counts = df["status"].value_counts().to_dict()

        critical = int(sev_counts.get("Critical", 0))
        high = int(sev_counts.get("High", 0))
        medium = int(sev_counts.get("Medium", 0))
        low = int(sev_counts.get("Low", 0))

        resolved = int(status_counts.get("Resolved", 0)) + int(status_counts.get("Closed", 0))
        open_cnt = int(status_counts.get("Open", 0))
        in_progress = int(status_counts.get("In Progress", 0))

        resolution_rate = round((resolved / total * 100), 1) if total > 0 else 0.0

        # Average resolution time
        res_times = df["resolution_time"].dropna()
        avg_res_time = round(float(res_times.mean()), 1) if not res_times.empty else 0.0

        demo_count = int(df["is_demo"].sum()) if "is_demo" in df.columns else 0

        return {
            "total_incidents": total,
            "critical_incidents": critical,
            "high_incidents": high,
            "medium_incidents": medium,
            "low_incidents": low,
            "open_incidents": open_cnt,
            "in_progress_incidents": in_progress,
            "resolved_incidents": resolved,
            "closed_incidents": int(status_counts.get("Closed", 0)),
            "resolution_rate": resolution_rate,
            "avg_resolution_time": avg_res_time,
            "is_demo_count": demo_count,
            "has_records": total > 0
        }

    @staticmethod
    def get_trends(df):
        """Trends over time: daily count, plus breakdown by severity"""
        if df.empty:
            return {"dates": [], "counts": [], "severity_trends": {}}

        temp = df.copy()
        temp["date_day"] = pd.to_datetime(temp["incident_date"]).dt.strftime("%Y-%m-%d")
        
        # Overall daily trend
        daily = temp.groupby("date_day").size().reset_index(name="count")
        daily = daily.sort_values("date_day")

        # Severity breakdown over time
        sev_pivot = temp.pivot_table(index="date_day", columns="severity", values="incident_id", aggfunc="count", fill_value=0)
        sev_trends = {}
        for sev in ["Critical", "High", "Medium", "Low"]:
            sev_trends[sev] = [int(v) for v in sev_pivot[sev].tolist()] if sev in sev_pivot.columns else [0] * len(daily)

        return {
            "dates": daily["date_day"].tolist(),
            "counts": [int(c) for c in daily["count"].tolist()],
            "severity_trends": sev_trends
        }

    @staticmethod
    def get_category_distribution(df):
        if df.empty:
            return {"categories": [], "counts": []}
        cats = df["incident_type"].value_counts()
        return {
            "categories": cats.index.tolist(),
            "counts": [int(v) for v in cats.values.tolist()]
        }

    @staticmethod
    def get_severity_distribution(df):
        if df.empty:
            return {"severities": ["Critical", "High", "Medium", "Low"], "counts": [0, 0, 0, 0]}
        order = ["Critical", "High", "Medium", "Low"]
        counts = df["severity"].value_counts()
        return {
            "severities": order,
            "counts": [int(counts.get(s, 0)) for s in order]
        }

    @staticmethod
    def get_source_distribution(df):
        if df.empty:
            return {"sources": [], "counts": []}
        sources = df["source"].value_counts()
        return {
            "sources": sources.index.tolist(),
            "counts": [int(v) for v in sources.values.tolist()]
        }

    @staticmethod
    def get_status_distribution(df):
        if df.empty:
            return {"statuses": [], "counts": []}
        statuses = df["status"].value_counts()
        return {
            "statuses": statuses.index.tolist(),
            "counts": [int(v) for v in statuses.values.tolist()]
        }

    @staticmethod
    def get_heatmap_matrix(df):
        """Matrix of Day of Week (Mon-Sun) vs Hour of Day (0-23) for incident frequency"""
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        matrix = [[0 for _ in range(24)] for _ in range(7)]

        if df.empty:
            return {"days": days, "hours": list(range(24)), "matrix": matrix, "max_val": 0}

        temp = df.copy()
        dt_series = pd.to_datetime(temp["incident_date"])
        temp["dow"] = dt_series.dt.dayofweek # 0 is Monday
        temp["hour"] = dt_series.dt.hour

        grouped = temp.groupby(["dow", "hour"]).size().reset_index(name="count")
        max_val = 0
        for _, row in grouped.iterrows():
            d = int(row["dow"])
            h = int(row["hour"])
            c = int(row["count"])
            if 0 <= d < 7 and 0 <= h < 24:
                matrix[d][h] = c
                if c > max_val:
                    max_val = c

        return {
            "days": days,
            "hours": list(range(24)),
            "matrix": matrix,
            "max_val": max_val
        }
