// CyberShield AI CSV Upload & Cleaning 15-Stage Workflow Engine
let selectedFile = null;
let currentPreviewData = null;

document.addEventListener("DOMContentLoaded", () => {
  initDropZone();
  initUploadButtons();
});

function initDropZone() {
  const dropZone = document.getElementById("csvDropZone");
  const fileInput = document.getElementById("csvFileInput");
  if (!dropZone || !fileInput) return;

  dropZone.addEventListener("click", () => fileInput.click());

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("border-info");
    dropZone.style.background = "rgba(0, 229, 255, 0.05)";
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("border-info");
    dropZone.style.background = "transparent";
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("border-info");
    dropZone.style.background = "transparent";
    if (e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
      handleFileSelected(fileInput.files[0]);
    }
  });
}

function handleFileSelected(file) {
  // Validate extension
  if (!file.name.toLowerCase().endsWith(".csv")) {
    showToast("Invalid file type. Please upload a .csv file.", "danger");
    return;
  }

  // Validate size (5MB)
  if (file.size > 5 * 1024 * 1024) {
    showToast("File size exceeds 5MB limit.", "danger");
    return;
  }

  selectedFile = file;
  document.getElementById("selectedFileName").innerText = file.name;
  document.getElementById("selectedFileSize").innerText = `${(file.size / 1024).toFixed(1)} KB`;
  document.getElementById("fileInfoCard").classList.remove("d-none");

  // Automatically start stage 3-9 inspection & preview
  previewCsvFile(file);
}

async function previewCsvFile(file) {
  const previewContainer = document.getElementById("uploadInspectionSection");
  previewContainer.classList.remove("d-none");
  document.getElementById("inspectionLoadingSpinner").classList.remove("d-none");
  document.getElementById("inspectionDetails").classList.add("d-none");

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/api/upload/preview", {
      method: "POST",
      body: formData
    });
    const json = await res.json();

    document.getElementById("inspectionLoadingSpinner").classList.add("d-none");

    if (!json.success) {
      showToast(json.error || "CSV parsing error", "danger");
      return;
    }

    currentPreviewData = json;
    renderInspectionSummary(json);

  } catch (err) {
    document.getElementById("inspectionLoadingSpinner").classList.add("d-none");
    showToast("Server error during CSV validation", "danger");
  }
}

function renderInspectionSummary(data) {
  document.getElementById("inspectionDetails").classList.remove("d-none");
  document.getElementById("summaryTotalRows").innerText = data.total_rows.toLocaleString();
  document.getElementById("summaryDuplicates").innerText = data.duplicate_count;
  document.getElementById("summaryInvalidDates").innerText = data.invalid_date_count;
  document.getElementById("summaryInvalidSeverities").innerText = data.invalid_severity_count;

  // Schema Validation Check
  const schemaBadge = document.getElementById("schemaValidationBadge");
  const btnProceed = document.getElementById("btnProceedImport");

  if (data.has_required) {
    schemaBadge.className = "alert alert-success d-flex align-items-center gap-2 mb-3";
    schemaBadge.innerHTML = `<i class="fas fa-check-circle fs-5"></i>
      <div><strong>Valid Schema:</strong> All 5 required columns (<code>date, incident_type, severity, source, status</code>) detected.</div>`;
    btnProceed.disabled = false;
  } else {
    schemaBadge.className = "alert alert-danger d-flex align-items-center gap-2 mb-3";
    schemaBadge.innerHTML = `<i class="fas fa-triangle-exclamation fs-5"></i>
      <div><strong>Schema Error:</strong> Missing mandatory column(s): <code>${data.missing_required.join(", ")}</code>. Please adjust header in CSV before importing.</div>`;
    btnProceed.disabled = true;
  }

  // Render Preview Table
  const tableHead = document.getElementById("previewTableHead");
  const tableBody = document.getElementById("previewTableBody");

  if (data.columns && data.columns.length > 0) {
    tableHead.innerHTML = `<tr>${data.columns.map(c => `<th>${c}</th>`).join("")}</tr>`;
    tableBody.innerHTML = data.preview.map(row => {
      return `<tr>${data.columns.map(c => `<td>${escapeHtml(row[c] !== undefined && row[c] !== null ? row[c] : "")}</td>`).join("")}</tr>`;
    }).join("");
  }
}

function initUploadButtons() {
  document.getElementById("btnProceedImport")?.addEventListener("click", () => {
    const confirmModal = new bootstrap.Modal(document.getElementById("confirmImportModal"));
    confirmModal.show();
  });

  document.getElementById("btnExecuteImport")?.addEventListener("click", executeImport);
}

async function executeImport() {
  if (!selectedFile) return;

  const btn = document.getElementById("btnExecuteImport");
  btn.disabled = true;
  btn.innerHTML = `<i class="fas fa-spinner fa-spin me-2"></i>Importing into SQLite...`;

  const formData = new FormData();
  formData.append("file", selectedFile);
  formData.append("deduplicate", document.getElementById("optDeduplicate").checked);
  formData.append("fill_missing", document.getElementById("optFillMissing").checked);
  formData.append("normalize_enums", document.getElementById("optNormalizeEnums").checked);

  try {
    const res = await fetch("/api/upload/import", {
      method: "POST",
      body: formData
    });
    const json = await res.json();

    bootstrap.Modal.getInstance(document.getElementById("confirmImportModal"))?.hide();
    btn.disabled = false;
    btn.innerHTML = `<i class="fas fa-file-import me-1"></i>Confirm & Ingest`;

    if (!json.success) {
      showToast(json.error || "Import failed", "danger");
      return;
    }

    renderImportSuccess(json);

  } catch (err) {
    btn.disabled = false;
    btn.innerHTML = `<i class="fas fa-file-import me-1"></i>Confirm & Ingest`;
    showToast("Network failure during import", "danger");
  }
}

function renderImportSuccess(result) {
  document.getElementById("uploadInspectionSection").classList.add("d-none");
  const successSection = document.getElementById("importSuccessSection");
  successSection.classList.remove("d-none");

  document.getElementById("resultImportedCount").innerText = result.imported_count;
  document.getElementById("resultRejectedCount").innerText = result.rejected_count;

  const reasonsList = document.getElementById("rejectedReasonsList");
  if (result.reasons && result.reasons.length > 0) {
    reasonsList.innerHTML = result.reasons.map(r => `<li>${escapeHtml(r)}</li>`).join("");
    document.getElementById("rejectionNoticeCard").classList.remove("d-none");
  } else {
    document.getElementById("rejectionNoticeCard").classList.add("d-none");
  }

  showToast(`Successfully ingested ${result.imported_count} incident records`, "success");
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
