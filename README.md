# 🛡️ CyberShield AI

### Advanced Cybersecurity Incident Data Analysis & Visualization Platform

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![Chart.js](https://img.shields.io/badge/Chart.js-4.4-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white)](https://chartjs.org)
[![ReportLab](https://img.shields.io/badge/ReportLab-PDF-DC2626?style=for-the-badge&logo=adobeacrobatreader&logoColor=white)](https://www.reportlab.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![Tests](https://img.shields.io/badge/Tests-16%20Passed-22C55E?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org)

**"Turn Cyber Threats Into Actionable Intelligence."**

CyberShield AI is a full-stack, responsive, and visually stunning web platform designed for Security Operations Center (SOC) incident analysis. It ingests cybersecurity incident datasets, detects anomalous patterns, normalizes disparate formats, evaluates threat prioritization scores (0–100), visualizes temporal trends, and generates downloadable audit-grade ReportLab PDF reports.

Designed for college mini-projects, academic demonstrations, and cybersecurity developer portfolios.

---

## 📸 Key Capabilities & Visual Showcase

* 🎛️ **Futuristic Cyber SOC Interface**: Dark cyberpunk mode and Daylight Clean theme with glowing neon accents (`#00E5FF`, `#3B82F6`, `#8B5CF6`, `#EF4444`, `#22C55E`), glassmorphism cards, and smooth micro-animations.
* 📊 **Security Operations Center Dashboard**: 7 real-time KPI metrics (Total incidents, Critical severity, High risk, Open alerts, Resolved events, Resolution rate %, Mean resolution hours) and 7 interactive visualizations powered by Chart.js.
* 🗓️ **Temporal Heatmap Matrix**: Identifies recurring threat vectors across 7 days of the week and 24 hourly buckets to uncover off-hours reconnaissance.
* 🛡️ **Full Incident CRUD Management**: Complete search, multi-column sorting, pagination, add, view details, edit, delete with confirmation, and CSV exports.
* 🧹 **15-Stage CSV Cleaning & Ingestion Pipeline**: Drag-and-drop CSV dropzone, safe non-executing parser, schema validation (`date`, `incident_type`, `severity`, `source`, `status`), duplicate detection, enum normalization, missing-value mitigation, and transactional ACID SQLite persistence.
* 🧠 **Transparent Heuristic Prioritization Score (0–100)**: Evaluates incident triage priority using four documented, deterministic factors: Severity Tier (max 45), Status Urgency (max 25), Crown Jewel Asset Impact (max 15), and Alert Aging (max 15).
* 🤖 **AI Cyber Security Advisor (Optional Gemini API)**: Ingests incident telemetry to deliver executive security posture assessments and tactical mitigation advice. Works 100% offline out-of-the-box with a built-in heuristic reasoning engine, and optionally connects to Google Gemini API when an API key is provided!
* 📄 **Dynamic ReportLab PDF Generator**: Compiles executive incident audit dossiers on-the-fly directly to binary PDF with styled summary tables, KPI grids, and tactical recommendations.

---

## 🏗️ Project Architecture & Directory Structure

```text
cyber security/
├── app.py                      # Flask Application entry point & REST API routes
├── config.py                   # Environment configuration (Dev, Test, Prod)
├── requirements.txt            # Python dependency specification
├── README.md                   # Comprehensive documentation & setup guide
├── .env.example                # Template for environment secrets
├── .gitignore                  # Source control exclusion rules
│
├── database/
│   └── db_manager.py           # SQLite connection pool, schema, indexed CRUD
│
├── services/
│   ├── data_cleaning.py        # 15-stage CSV audit, deduplication & normalization
│   ├── analytics.py            # KPI metrics, timelines, distributions & heatmap matrix
│   ├── threat_analysis.py      # Category deep dive, 0-100 heuristic scoring & AI advisor
│   └── report_generator.py     # ReportLab dynamic PDF report generation engine
│
├── templates/
│   ├── base.html               # Shared master layout with sidebar, navbar & clock
│   ├── index.html              # Modern cybersecurity hero landing page
│   ├── dashboard.html          # SOC Security Dashboard with 7 KPI cards & 7 charts
│   ├── incidents.html          # Incident Explorer with CRUD modals & pagination
│   ├── upload.html             # Drag-and-drop CSV 15-stage cleaning pipeline
│   ├── threat_analysis.html    # Deep-dive category vectors & heuristic prioritization
│   ├── visualizations.html     # Interactive Visualization Studio
│   ├── reports.html            # Dynamic PDF and CSV audit reporting center
│   ├── about.html              # Academic methodology, architecture & credits
│   ├── settings.html           # Theme selector, demo data controls & API keys
│   ├── 404.html                # Custom futuristic 404 error page
│   └── 500.html                # Custom 500 server exception page
│
├── static/
│   ├── css/
│   │   └── style.css           # Cyberpunk design system, glassmorphism & responsive layout
│   └── js/
│       ├── main.js             # Theme toggle, live clock & global toast notifications
│       ├── dashboard.js        # Chart.js instances, filter synchronization & heatmap
│       ├── incidents.js        # Table rendering, CRUD event listeners & search
│       ├── upload.js           # Drag-and-drop dropzone & 15-stage cleaning logic
│       ├── visualizations.js   # Dynamic chart builder, PNG export & CSV data dump
│       └── settings.js         # Theme persistence, API key storage & demo resets
│
├── data/
│   └── sample_incidents.csv    # 40+ Realistic cybersecurity incident demonstration records
│
├── tests/
│   ├── test_routes.py          # Route accessibility, CRUD lifecycle & API tests
│   ├── test_analytics.py       # KPI metrics, empty dataframe safety & PDF engine tests
│   └── test_upload.py          # CSV parsing, schema checking & validation tests
│
└── instance/
    └── cybersecurity.db        # SQLite persistent database (created automatically)
```

---

## 🚀 Quick Start & Installation Instructions

Follow these step-by-step instructions on **Windows (Command Prompt / PowerShell)** or **VS Code**.

### Step 1: Open Terminal in Project Directory
Open **PowerShell** or **Command Prompt** and navigate to your project directory:
```powershell
cd "c:\Users\HP\Downloads\cyber security"
```

### Step 2: Create a Python Virtual Environment
```powershell
python -m venv .venv
```

### Step 3: Activate the Virtual Environment
* **On Windows PowerShell:**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
  *(If PowerShell displays an Execution_Policy notice, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and then run the command again)*
* **On Windows Command Prompt (CMD):**
  ```cmd
  .venv\Scripts\activate.bat
  ```

### Step 4: Install Dependencies
```powershell
python -m pip install -r requirements.txt
```

### Step 5: Start the CyberShield AI Application
```powershell
python app.py
```

### Step 6: Open the Web Application
Open your browser and navigate to:
👉 **`http://127.0.0.1:5000`**

---

## 🔑 AI API Key Configuration (Google Gemini)

CyberShield AI comes equipped with a hybrid intelligence engine:

1. **Built-in Intelligent Heuristic Engine (Zero Key Required)**: By default, CyberShield AI operates 100% out of the box using its local deterministic rules to classify threat postures and tactical recommendations.
2. **Google Gemini AI API Key (Optional Enhancement)**: If you provide a Google Gemini API key, CyberShield AI queries Gemini to deliver natural language security intelligence reports.

### How to Add Your API Key:
* **Option A (Via Web Interface)**:
  1. Open CyberShield AI in your browser.
  2. Navigate to **Settings** (`/settings`) from the left sidebar.
  3. Under **Google Gemini API Key**, paste your API key and click **Save Preferences**.
* **Option B (Via `.env` file)**:
  1. Copy `.env.example` to `.env`:
     ```powershell
     copy .env.example .env
     ```
  2. Open `.env` and set:
     ```env
     GEMINI_API_KEY=your_actual_gemini_api_key_here
     ```

---

## 📤 Step-by-Step Guide: How to Upload to GitHub

You can upload your entire CyberShield AI project to GitHub in either of two straightforward ways:

### Method 1: Using Git in the Terminal (Recommended & Fastest)

1. Open your terminal in the project folder:
   ```powershell
   cd "c:\Users\HP\Downloads\cyber security"
   ```
2. Initialize Git:
   ```powershell
   git init
   ```
3. Add all files to staging:
   ```powershell
   git add .
   ```
4. Commit your files:
   ```powershell
   git commit -m "Initial commit: CyberShield AI Platform"
   ```
5. Create a new repository on [GitHub.com](https://github.com/new) named `cybershield-ai` (keep it Public or Private).
6. Link your local project to GitHub and push (replace `YOUR-USERNAME` with your GitHub username):
   ```powershell
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/cybershield-ai.git
   git push -u origin main
   ```

### Method 2: Upload Directly on GitHub Website

1. Go to [GitHub.com](https://github.com/new) and create a new repository (e.g. `cybershield-ai`).
2. On the empty repository page, click the link: **"uploading an existing file"**.
3. Drag and drop the files and folders (`app.py`, `config.py`, `requirements.txt`, `README.md`, `templates/`, `static/`, `services/`, `database/`, `data/`, `tests/`) into the GitHub upload box.
4. Click **"Commit changes"**.

---

## 🧪 Automated Testing

CyberShield AI includes an automated test suite verifying route accessibility, CRUD persistence, data cleaning, ReportLab PDF generation, empty state handling, and threat score accuracy.

To run the automated tests:
```powershell
python -m pytest
```

Expected output:
```text
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1
collected 16 items

tests\test_analytics.py ....                                             [ 25%]
tests\test_routes.py .......                                             [ 68%]
tests\test_upload.py .....                                               [100%]

============================= 16 passed in 2.81s ==============================
```

---

## 📊 Heuristic Threat Prioritization Formula

Every logged incident receives a deterministic **Prioritization Score (0–100)**:

$$\text{Priority Score} = \text{Severity Weight} + \text{Status Factor} + \text{System Impact} + \text{Aging Factor}$$

1. **Severity Tier (Max 45 pts)**:
   * Critical $\rightarrow$ 45 pts
   * High $\rightarrow$ 30 pts
   * Medium $\rightarrow$ 15 pts
   * Low $\rightarrow$ 5 pts
2. **Status Factor (Max 25 pts)**:
   * Open (Unassigned alert) $\rightarrow$ +25 pts
   * In Progress (Active containment) $\rightarrow$ +15 pts
   * Resolved / Closed $\rightarrow$ 0 pts
3. **Target System Criticality (Max 15 pts)**:
   * High-value target (Domain Controller, Database, Backup SAN, S3, Core Router) $\rightarrow$ +15 pts
   * Standard asset $\rightarrow$ +5 pts
4. **Alert Aging Factor (Max 15 pts)**:
   * Unresolved alert aging $>7$ days $\rightarrow$ +15 pts
   * Unresolved alert aging $>2$ days $\rightarrow$ +10 pts
   * Recent alert $\rightarrow$ +5 pts

---

## 🔒 Security & Academic Scope

* **Server-side Validation**: Strict verification of file extensions, 5MB upload size limits, and sanitization of text inputs.
* **SQL Injection Prevention**: 100% parameterized queries using SQLite prepared statements.
* **Non-Execution Safeguard**: Uploaded CSV files are parsed safely via pandas streams without executing system commands.
* **Academic Disclaimer**: CyberShield AI demonstrates incident telemetry analytics, data cleaning, and reporting automation. It is not an inline packet inspection daemon or replacement for enterprise commercial SIEMs.

---

## 👨‍💻 Developer & Project Credits

* **Project**: CyberShield AI &ndash; Cybersecurity Incident Data Analysis and Visualization Platform
* **Purpose**: Academic Mini-Project & Professional Portfolio Demonstration
* **Version**: 2.5.0 Production Ready
* **License**: MIT Open Academic License
