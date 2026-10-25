// CyberShield AI Incident Explorer & CRUD Controller
let currentPage = 1;
let currentSortBy = "incident_date";
let currentSortOrder = "DESC";
let incidentModalInstance = null;
let viewModalInstance = null;
let deleteModalInstance = null;
let activeDeleteId = null;

document.addEventListener("DOMContentLoaded", () => {
  // Check URL parameters for search or filters
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get("search")) {
    const sInput = document.getElementById("searchIncidentInput");
    if (sInput) sInput.value = urlParams.get("search");
  }

  initModals();
  initIncidentEvents();
  loadIncidents();
});

function initModals() {
  const incModalEl = document.getElementById("incidentFormModal");
  if (incModalEl) incidentModalInstance = new bootstrap.Modal(incModalEl);

  const viewModalEl = document.getElementById("incidentDetailModal");
  if (viewModalEl) viewModalInstance = new bootstrap.Modal(viewModalEl);

  const delModalEl = document.getElementById("confirmDeleteModal");
  if (delModalEl) deleteModalInstance = new bootstrap.Modal(delModalEl);
}

function initIncidentEvents() {
  document.getElementById("btnApplyFilters")?.addEventListener("click", () => {
    currentPage = 1;
    loadIncidents();
  });

  document.getElementById("searchIncidentInput")?.addEventListener("input", debounce(() => {
    currentPage = 1;
    loadIncidents();
  }, 400));

  document.getElementById("filterCategory")?.addEventListener("change", () => {
    currentPage = 1;
    loadIncidents();
  });

  document.getElementById("filterSeverity")?.addEventListener("change", () => {
    currentPage = 1;
    loadIncidents();
  });

  document.getElementById("filterStatus")?.addEventListener("change", () => {
    currentPage = 1;
    loadIncidents();
  });

  // Table Sort Header Clicks
  document.querySelectorAll("th.sortable").forEach(th => {
    th.addEventListener("click", () => {
      const field = th.getAttribute("data-sort");
      if (currentSortBy === field) {
        currentSortOrder = currentSortOrder === "ASC" ? "DESC" : "ASC";
      } else {
        currentSortBy = field;
        currentSortOrder = "DESC";
      }
      updateSortIcons();
      loadIncidents();
    });
  });

  // Add Incident Button
  document.getElementById("btnOpenAddIncident")?.addEventListener("click", () => {
    resetIncidentForm();
    document.getElementById("incidentFormModalTitle").innerText = "Log New Security Incident";
    document.getElementById("incidentFormId").value = "";
    incidentModalInstance.show();
  });

  // Save Incident Form Submit
  document.getElementById("incidentForm")?.addEventListener("submit", handleSaveIncident);

  // Confirm Delete Button Click
  document.getElementById("btnConfirmDelete")?.addEventListener("click", handleDeleteIncident);

  // Export Filtered Incidents to CSV
  document.getElementById("btnExportFilteredCsv")?.addEventListener("click", () => {
    const query = buildIncidentQuery();
    window.location.href = `/api/reports/export?${query}`;
  });
}

function updateSortIcons() {
  document.querySelectorAll("th.sortable i").forEach(icon => {
    icon.className = "fas fa-sort text-muted ms-1";
  });
  const activeTh = document.querySelector(`th.sortable[data-sort="${currentSortBy}"] i`);
  if (activeTh) {
    activeTh.className = `fas fa-sort-${currentSortOrder === "ASC" ? "up" : "down"} text-info ms-1`;
  }
}

function buildIncidentQuery() {
  const params = new URLSearchParams();
  const search = document.getElementById("searchIncidentInput")?.value.trim();
  const cat = document.getElementById("filterCategory")?.value;
  const sev = document.getElementById("filterSeverity")?.value;
  const status = document.getElementById("filterStatus")?.value;
  const startDate = document.getElementById("filterStartDate")?.value;
  const endDate = document.getElementById("filterEndDate")?.value;

  params.append("page", currentPage);
  params.append("per_page", 10);
  params.append("sort_by", currentSortBy);
  params.append("sort_order", currentSortOrder);

  if (search) params.append("search", search);
  if (cat && cat !== "all") params.append("category", cat);
  if (sev && sev !== "all") params.append("severity", sev);
  if (status && status !== "all") params.append("status", status);
  if (startDate) params.append("start_date", startDate);
  if (endDate) params.append("end_date", endDate);

  return params.toString();
}

async function loadIncidents() {
  const tbody = document.getElementById("incidentsTableBody");
  tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted"><i class="fas fa-spinner fa-spin me-2"></i>Loading security incidents...</td></tr>`;

  try {
    const query = buildIncidentQuery();
    const res = await fetch(`/api/incidents?${query}`);
    const json = await res.json();

    if (!json.success || json.data.items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" class="text-center py-5 text-muted">
        <i class="fas fa-shield-halved fs-3 mb-2 d-block opacity-50"></i>
        No incidents match the active search criteria or filters.
      </td></tr>`;
      renderPagination(1, 1);
      return;
    }

    renderTableRows(json.data.items);
    renderPagination(json.data.page, json.data.pages, json.data.total);

  } catch (err) {
    console.error("Load incidents error:", err);
    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-danger"><i class="fas fa-triangle-exclamation me-2"></i>Failed to load incident records.</td></tr>`;
  }
}

function renderTableRows(items) {
  const tbody = document.getElementById("incidentsTableBody");
  tbody.innerHTML = items.map(item => {
    const sevBadge = `badge-${item.severity.toLowerCase()}`;
    const statusClass = `badge-${item.status.toLowerCase().replace(" ", "-")}`;

    return `
      <tr>
        <td class="font-monospace fw-bold text-info">${escapeHtml(item.incident_id)}</td>
        <td class="text-muted" style="white-space: nowrap;">${escapeHtml(item.incident_date.substring(0, 16))}</td>
        <td><span class="fw-semibold">${escapeHtml(item.incident_type)}</span></td>
        <td><span class="badge ${sevBadge}">${escapeHtml(item.severity)}</span></td>
        <td class="text-muted">${escapeHtml(item.source)}</td>
        <td><code>${escapeHtml(item.affected_system || "N/A")}</code></td>
        <td><span class="badge ${statusClass}">${escapeHtml(item.status)}</span></td>
        <td class="text-end">
          <button class="btn btn-sm btn-outline-info me-1" onclick="viewIncident('${item.incident_id}')" title="View Details">
            <i class="fas fa-eye"></i>
          </button>
          <button class="btn btn-sm btn-outline-warning me-1" onclick="editIncident('${item.incident_id}')" title="Edit Incident">
            <i class="fas fa-edit"></i>
          </button>
          <button class="btn btn-sm btn-outline-danger" onclick="confirmDeleteIncident('${item.incident_id}')" title="Delete">
            <i class="fas fa-trash-alt"></i>
          </button>
        </td>
      </tr>
    `;
  }).join("");
}

function renderPagination(page, pages, total = 0) {
  const container = document.getElementById("incidentsPagination");
  if (!container) return;

  document.getElementById("incidentCountSummary")?.innerText = `Showing page ${page} of ${pages} (${total} total records)`;

  if (pages <= 1) {
    container.innerHTML = "";
    return;
  }

  let html = `<ul class="pagination pagination-sm m-0">`;
  html += `<li class="page-item ${page === 1 ? 'disabled' : ''}">
    <button class="page-link" onclick="goToPage(${page - 1})"><i class="fas fa-chevron-left"></i></button>
  </li>`;

  for (let p = Math.max(1, page - 2); p <= Math.min(pages, page + 2); p++) {
    html += `<li class="page-item ${p === page ? 'active' : ''}">
      <button class="page-link" onclick="goToPage(${p})">${p}</button>
    </li>`;
  }

  html += `<li class="page-item ${page === pages ? 'disabled' : ''}">
    <button class="page-link" onclick="goToPage(${page + 1})"><i class="fas fa-chevron-right"></i></button>
  </li></ul>`;

  container.innerHTML = html;
}

function goToPage(p) {
  currentPage = p;
  loadIncidents();
}

async function viewIncident(id) {
  try {
    const res = await fetch(`/api/incidents/${id}`);
    const json = await res.json();
    if (!json.success) {
      showToast(json.error || "Incident not found", "danger");
      return;
    }
    const item = json.incident;
    document.getElementById("viewModalId").innerText = item.incident_id;
    document.getElementById("viewModalDate").innerText = item.incident_date;
    document.getElementById("viewModalType").innerText = item.incident_type;
    document.getElementById("viewModalSeverity").innerHTML = `<span class="badge badge-${item.severity.toLowerCase()}">${item.severity}</span>`;
    document.getElementById("viewModalStatus").innerHTML = `<span class="badge badge-${item.status.toLowerCase().replace(' ', '-')}">${item.status}</span>`;
    document.getElementById("viewModalSource").innerText = item.source;
    document.getElementById("viewModalSystem").innerText = item.affected_system || "N/A";
    document.getElementById("viewModalResolution").innerText = item.resolution_time ? `${item.resolution_time} hours` : "Not resolved yet";
    document.getElementById("viewModalDescription").innerText = item.description || "No description provided.";
    document.getElementById("viewModalDemoBadge").innerHTML = item.is_demo ? `<span class="badge bg-secondary">Synthetic Demonstration Record</span>` : `<span class="badge bg-success">Imported Production Record</span>`;

    viewModalInstance.show();
  } catch (err) {
    showToast("Error retrieving incident details", "danger");
  }
}

async function editIncident(id) {
  try {
    const res = await fetch(`/api/incidents/${id}`);
    const json = await res.json();
    if (!json.success) {
      showToast(json.error || "Incident not found", "danger");
      return;
    }
    const item = json.incident;
    document.getElementById("incidentFormModalTitle").innerText = `Edit Incident ${item.incident_id}`;
    document.getElementById("incidentFormId").value = item.incident_id;
    document.getElementById("formDate").value = item.incident_date.replace(" ", "T").substring(0, 16);
    document.getElementById("formType").value = item.incident_type;
    document.getElementById("formSeverity").value = item.severity;
    document.getElementById("formStatus").value = item.status;
    document.getElementById("formSource").value = item.source;
    document.getElementById("formSystem").value = item.affected_system || "";
    document.getElementById("formResolutionTime").value = item.resolution_time !== null ? item.resolution_time : "";
    document.getElementById("formDescription").value = item.description || "";

    incidentModalInstance.show();
  } catch (err) {
    showToast("Error loading incident for editing", "danger");
  }
}

async function handleSaveIncident(e) {
  e.preventDefault();
  const formId = document.getElementById("incidentFormId").value;
  const isEdit = !!formId;

  const payload = {
    incident_date: document.getElementById("formDate").value.replace("T", " ") + ":00",
    incident_type: document.getElementById("formType").value,
    severity: document.getElementById("formSeverity").value,
    status: document.getElementById("formStatus").value,
    source: document.getElementById("formSource").value,
    affected_system: document.getElementById("formSystem").value,
    resolution_time: document.getElementById("formResolutionTime").value,
    description: document.getElementById("formDescription").value
  };

  const url = isEdit ? `/api/incidents/${formId}` : "/api/incidents";
  const method = isEdit ? "PUT" : "POST";

  try {
    const res = await fetch(url, {
      method: method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const json = await res.json();

    if (!json.success) {
      showToast(json.error || "Failed to save incident", "danger");
      return;
    }

    incidentModalInstance.hide();
    showToast(isEdit ? "Incident updated successfully" : "New incident logged", "success");
    loadIncidents();

  } catch (err) {
    showToast("Server communication error", "danger");
  }
}

function confirmDeleteIncident(id) {
  activeDeleteId = id;
  document.getElementById("deleteIncidentIdText").innerText = id;
  deleteModalInstance.show();
}

async function handleDeleteIncident() {
  if (!activeDeleteId) return;
  try {
    const res = await fetch(`/api/incidents/${activeDeleteId}`, { method: "DELETE" });
    const json = await res.json();
    if (!json.success) {
      showToast(json.error || "Failed to delete incident", "danger");
      return;
    }
    deleteModalInstance.hide();
    showToast(`Incident ${activeDeleteId} deleted`, "success");
    activeDeleteId = null;
    loadIncidents();
  } catch (err) {
    showToast("Failed to delete incident", "danger");
  }
}

function resetIncidentForm() {
  document.getElementById("incidentForm").reset();
  const now = new Date();
  const localIso = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
  document.getElementById("formDate").value = localIso;
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

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}
