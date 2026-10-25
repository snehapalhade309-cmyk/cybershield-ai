import pandas as pd
import numpy as np
from datetime import datetime
import json
import urllib.request
import urllib.error

CRITICAL_SYSTEM_KEYWORDS = [
    "domain controller", "active directory", "database", "payment", 
    "backup", "san", "root", "firewall", "router", "core", "s3", "kiosk"
]

class ThreatAnalysisService:
    @staticmethod
    def calculate_prioritization_score(incident):
        """
        Calculates a transparent, rule-based Prioritization Score (0-100).
        Formula:
        Score = Severity_Weight (max 45) 
              + Status_Factor (max 25) 
              + System_Criticality (max 15) 
              + Age_Recency_Factor (max 15)
        """
        sev = str(incident.get("severity", "")).capitalize()
        status = str(incident.get("status", "")).capitalize()
        system = str(incident.get("affected_system", "")).lower()
        date_str = str(incident.get("incident_date", ""))

        breakdown = {
            "severity_weight": 0,
            "status_factor": 0,
            "system_criticality": 0,
            "age_factor": 0,
            "formula_notes": []
        }

        # 1. Severity Weight (max 45)
        if sev == "Critical":
            breakdown["severity_weight"] = 45
            breakdown["formula_notes"].append("Critical severity tier (+45)")
        elif sev == "High":
            breakdown["severity_weight"] = 30
            breakdown["formula_notes"].append("High severity tier (+30)")
        elif sev == "Medium":
            breakdown["severity_weight"] = 15
            breakdown["formula_notes"].append("Medium severity tier (+15)")
        else:
            breakdown["severity_weight"] = 5
            breakdown["formula_notes"].append("Low severity tier (+5)")

        # 2. Status Factor (max 25)
        if status == "Open":
            breakdown["status_factor"] = 25
            breakdown["formula_notes"].append("Incident active & unassigned (+25)")
        elif status == "In Progress":
            breakdown["status_factor"] = 15
            breakdown["formula_notes"].append("Incident under active containment (+15)")
        else:
            breakdown["status_factor"] = 0
            breakdown["formula_notes"].append("Incident resolved or closed (+0)")

        # 3. System Criticality (max 15)
        matched_kw = [kw for kw in CRITICAL_SYSTEM_KEYWORDS if kw in system]
        if matched_kw:
            breakdown["system_criticality"] = 15
            breakdown["formula_notes"].append(f"High-value target asset ({matched_kw[0]}) (+15)")
        else:
            breakdown["system_criticality"] = 5
            breakdown["formula_notes"].append("Standard tier endpoint/network device (+5)")

        # 4. Age & Escalation Factor (max 15)
        try:
            inc_dt = pd.to_datetime(date_str)
            age_days = (datetime.now() - inc_dt).days
            if status in ["Open", "In Progress"]:
                if age_days > 7:
                    breakdown["age_factor"] = 15
                    breakdown["formula_notes"].append("Aging unresolved alert (>7 days) (+15)")
                elif age_days > 2:
                    breakdown["age_factor"] = 10
                    breakdown["formula_notes"].append("Aging unresolved alert (>2 days) (+10)")
                else:
                    breakdown["age_factor"] = 5
                    breakdown["formula_notes"].append("Recent unresolved alert (+5)")
            else:
                breakdown["age_factor"] = 0
                breakdown["formula_notes"].append("Incident already closed (+0)")
        except Exception:
            breakdown["age_factor"] = 5

        total_score = sum([
            breakdown["severity_weight"],
            breakdown["status_factor"],
            breakdown["system_criticality"],
            breakdown["age_factor"]
        ])
        total_score = min(100, max(0, total_score))

        # Risk level classification
        if total_score >= 80:
            urgency = "CRITICAL PRIORITY"
            badge_class = "danger"
        elif total_score >= 60:
            urgency = "HIGH PRIORITY"
            badge_class = "warning"
        elif total_score >= 35:
            urgency = "MODERATE PRIORITY"
            badge_class = "info"
        else:
            urgency = "LOW PRIORITY"
            badge_class = "secondary"

        return {
            "score": total_score,
            "urgency": urgency,
            "badge_class": badge_class,
            "breakdown": breakdown,
            "explanation": f"Score of {total_score}/100: " + "; ".join(breakdown["formula_notes"])
        }

    @staticmethod
    def get_category_deep_dive(df):
        """Analyzes all incident categories, volume, average resolution, top sources"""
        if df.empty:
            return []

        categories = df["incident_type"].unique()
        result = []

        for cat in sorted(categories):
            sub = df[df["incident_type"] == cat]
            total = len(sub)
            crit_high = len(sub[sub["severity"].isin(["Critical", "High"])])
            open_count = len(sub[sub["status"] == "Open"])
            in_prog = len(sub[sub["status"] == "In Progress"])
            resolved = len(sub[sub["status"].isin(["Resolved", "Closed"])])

            res_times = sub["resolution_time"].dropna()
            avg_res = round(float(res_times.mean()), 1) if not res_times.empty else None

            top_source = sub["source"].mode().iloc[0] if not sub["source"].empty else "N/A"
            top_system = sub["affected_system"].mode().iloc[0] if not sub["affected_system"].empty else "N/A"

            # Determine risk rating
            risk_ratio = crit_high / total if total > 0 else 0
            if risk_ratio >= 0.6 or crit_high >= 5:
                risk_level = "Severe"
                risk_badge = "danger"
            elif risk_ratio >= 0.3:
                risk_level = "Elevated"
                risk_badge = "warning"
            else:
                risk_level = "Guarded"
                risk_badge = "info"

            result.append({
                "category": cat,
                "total_count": total,
                "critical_high_count": crit_high,
                "open_count": open_count,
                "in_progress_count": in_prog,
                "resolved_count": resolved,
                "avg_resolution_hours": avg_res,
                "top_source": top_source,
                "top_system": top_system,
                "risk_level": risk_level,
                "risk_badge": risk_badge
            })

        # Sort by total count descending
        result.sort(key=lambda x: x["total_count"], reverse=True)
        return result

    @staticmethod
    def get_prioritized_incidents(df, limit=20):
        """Returns incidents ranked by prioritization score"""
        if df.empty:
            return []

        records = df.to_dict(orient="records")
        scored_records = []
        for r in records:
            score_data = ThreatAnalysisService.calculate_prioritization_score(r)
            r_copy = dict(r)
            r_copy["priority_score"] = score_data["score"]
            r_copy["priority_urgency"] = score_data["urgency"]
            r_copy["priority_badge"] = score_data["badge_class"]
            r_copy["priority_explanation"] = score_data["explanation"]
            scored_records.append(r_copy)

        scored_records.sort(key=lambda x: x["priority_score"], reverse=True)
        return scored_records[:limit]

    @staticmethod
    def generate_ai_insights(df, api_key=""):
        """Generates executive security advisor insights using Gemini API or intelligent heuristic rules"""
        total = len(df)
        if total == 0:
            return {
                "source": "rule-engine",
                "summary": "No security records available in the active dataset. Ingest a dataset or explore sample telemetry to generate analytical threat intelligence.",
                "recommendations": ["Upload an incident dataset in CSV format or explore sample telemetry."],
                "threat_posture": "Undetermined"
            }

        crit_count = len(df[df["severity"] == "Critical"])
        high_count = len(df[df["severity"] == "High"])
        open_count = len(df[df["status"] == "Open"])
        top_cats = df["incident_type"].value_counts().head(3).to_dict()
        top_cat_str = ", ".join([f"{k} ({v})" for k, v in top_cats.items()])

        # If Gemini API key is provided, query Google Gemini API for deep cyber intelligence
        if api_key and len(api_key.strip()) > 10:
            try:
                prompt_text = (
                    f"You are CyberShield AI's senior SOC threat analyst. Analyze this incident dataset:\n"
                    f"Total Incidents: {total}, Critical: {crit_count}, High: {high_count}, Open: {open_count}.\n"
                    f"Dominant threat categories: {top_cat_str}.\n"
                    f"Provide a concise JSON response with keys: 'threat_posture' (e.g. Heightened, Critical, Guarded), "
                    f"'summary' (2-3 sentences), and 'recommendations' (list of 3 actionable defense mitigation steps)."
                )
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key.strip()}"
                headers = {"Content-Type": "application/json"}
                payload = json.dumps({
                    "contents": [{"parts": [{"text": prompt_text}]}],
                    "generationConfig": {"response_mime_type": "application/json"}
                }).encode("utf-8")
                
                req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=7) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    text = resp_data["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = json.loads(text)
                    return {
                        "source": "Gemini AI Threat Advisor",
                        "threat_posture": parsed.get("threat_posture", "Heightened"),
                        "summary": parsed.get("summary", "Analysis completed."),
                        "recommendations": parsed.get("recommendations", [])
                    }
            except Exception:
                pass # Gracefully fall back to local rule engine

        # Heuristic Rule Engine (Zero external dependency fallback)
        posture = "Guarded"
        if crit_count > 5 or (crit_count + high_count) / total > 0.4:
            posture = "High Risk / Heightened"
        elif crit_count > 0 or high_count > 5:
            posture = "Elevated Alert"

        summary = (
            f"Active incident telemetry tracks {total} total security events across endpoints and perimeter infrastructure. "
            f"High-priority vectors center around {top_cat_str}, with {crit_count} Critical and {high_count} High-severity incidents registered. "
            f"{open_count} incidents currently await triage and containment."
        )

        recs = [
            f"Immediate Containment: Prioritize triage of {open_count} open incidents, particularly on affected identity and storage assets.",
            f"Vector Hardening: Implement proactive defense rules targeting {list(top_cats.keys())[0] if top_cats else 'malicious access'}.",
            "Credential & Identity Audit: Enforce mandatory MFA verification and audit privileged administrator session durations across core infrastructure."
        ]

        return {
            "source": "CyberShield AI Heuristic Engine",
            "threat_posture": posture,
            "summary": summary,
            "recommendations": recs
        }
