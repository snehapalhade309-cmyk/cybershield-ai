// CyberShield AI Dashboard Visualizations Engine
let chartInstances = {};

document.addEventListener("DOMContentLoaded", () => {
  initDashboardFilters();
  loadDashboardData();

  window.addEventListener("themeChanged", () => {
    // Re-render charts on theme change to adjust text/grid colors
    loadDashboardData();
  });
});

function getChartTextColor() {
  return document.documentElement.getAttribute("data-theme") === "light" ? "#475569" : "#94a3b8";
}

function getChartGridColor() {
  return document.documentElement.getAttribute("data-theme") === "light" ? "rgba(203, 213, 225, 0.4)" : "rgba(148, 163, 184, 0.1)";
}

function initDashboardFilters() {
  const filterForm = document.getElementById("dashboardFilterForm");
  if (filterForm) {
    filterForm.addEventListener("submit", (e) => {
      e.preventDefault();
      loadDashboardData();
    });
  }

  const refreshBtn = document.getElementById("btnRefreshDashboard");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => {
      loadDashboardData();
      showToast("Security telemetry refreshed", "success");
    });
  }

  const exportBtn = document.getElementById("btnExportDashboardCsv");
  if (exportBtn) {
    exportBtn.addEventListener("click", () => {
      const query = buildFilterQuery();
      window.location.href = `/api/reports/export?${query}`;
    });
  }
}

function buildFilterQuery() {
  const params = new URLSearchParams();
  const start = document.getElementById("filterStartDate")?.value;
  const end = document.getElementById("filterEndDate")?.value;
  const cat = document.getElementById("filterCategory")?.value;
  const sev = document.getElementById("filterSeverity")?.value;
  const status = document.getElementById("filterStatus")?.value;

  if (start) params.append("start_date", start);
  if (end) params.append("end_date", end);
  if (cat && cat !== "all") params.append("category", cat);
  if (sev && sev !== "all") params.append("severity", sev);
  if (status && status !== "all") params.append("status", status);

  return params.toString();
}

async function loadDashboardData() {
  const query = buildFilterQuery();

  try {
    // Fetch all analytics concurrently
    const [resSummary, resTrends, resSev, resCats, resSources, resHeatmap] = await Promise.all([
      fetch(`/api/analytics/summary?${query}`).then(r => r.json()),
      fetch(`/api/analytics/trends?${query}`).then(r => r.json()),
      fetch(`/api/analytics/severity?${query}`).then(r => r.json()),
      fetch(`/api/analytics/categories?${query}`).then(r => r.json()),
      fetch(`/api/analytics/sources?${query}`).then(r => r.json()),
      fetch(`/api/analytics/heatmap?${query}`).then(r => r.json())
    ]);

    if (resSummary.success) renderKpis(resSummary.data);
    if (resTrends.success) renderTrendsChart(resTrends.data);
    if (resSev.success) renderSeverityChart(resSev.data);
    if (resCats.success) renderCategoryChart(resCats.data);
    if (resSources.success) renderSourceChart(resSources.data);
    if (resTrends.success) renderSeverityTrendChart(resTrends.data);
    if (resHeatmap.success) renderHeatmap(resHeatmap.data);

  } catch (err) {
    console.error("Dashboard data load error:", err);
    showToast("Failed to retrieve dashboard analytics", "danger");
  }
}

function renderKpis(data) {
  document.getElementById("kpiTotal").innerText = data.total_incidents.toLocaleString();
  document.getElementById("kpiCritical").innerText = data.critical_incidents.toLocaleString();
  document.getElementById("kpiHigh").innerText = data.high_incidents.toLocaleString();
  document.getElementById("kpiOpen").innerText = data.open_incidents.toLocaleString();
  document.getElementById("kpiResolved").innerText = data.resolved_incidents.toLocaleString();
  document.getElementById("kpiResolutionRate").innerText = `${data.resolution_rate}%`;
  document.getElementById("kpiAvgTime").innerText = `${data.avg_resolution_time}h`;

  const demoNotice = document.getElementById("demoDataNotice");
  if (demoNotice) {
    if (data.is_demo_count > 0) {
      demoNotice.classList.remove("d-none");
      demoNotice.querySelector(".demo-count").innerText = `${data.is_demo_count} synthetic demonstration records active`;
    } else {
      demoNotice.classList.add("d-none");
    }
  }
}

function destroyChart(name) {
  if (chartInstances[name]) {
    chartInstances[name].destroy();
  }
}

function renderTrendsChart(data) {
  destroyChart("trends");
  const ctx = document.getElementById("chartIncidentTrends")?.getContext("2d");
  if (!ctx) return;

  const textColor = getChartTextColor();
  const gridColor = getChartGridColor();

  chartInstances["trends"] = new Chart(ctx, {
    type: "line",
    data: {
      labels: data.dates,
      datasets: [{
        label: "Incident Volume",
        data: data.counts,
        borderColor: "#00E5FF",
        backgroundColor: "rgba(0, 229, 255, 0.15)",
        fill: true,
        tension: 0.35,
        borderWidth: 2.5,
        pointBackgroundColor: "#00E5FF",
        pointHoverRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: { ticks: { color: textColor }, grid: { color: gridColor } },
        y: { ticks: { color: textColor, precision: 0 }, grid: { color: gridColor }, beginAtZero: true }
      }
    }
  });
}

function renderSeverityTrendChart(data) {
  destroyChart("sevTrends");
  const ctx = document.getElementById("chartSeverityTrends")?.getContext("2d");
  if (!ctx) return;

  const textColor = getChartTextColor();
  const gridColor = getChartGridColor();
  const st = data.severity_trends || {};

  chartInstances["sevTrends"] = new Chart(ctx, {
    type: "bar",
    data: {
      labels: data.dates,
      datasets: [
        { label: "Critical", data: st["Critical"] || [], backgroundColor: "#EF4444" },
        { label: "High", data: st["High"] || [], backgroundColor: "#F59E0B" },
        { label: "Medium", data: st["Medium"] || [], backgroundColor: "#3B82F6" },
        { label: "Low", data: st["Low"] || [], backgroundColor: "#22C55E" }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { stacked: true, ticks: { color: textColor }, grid: { color: gridColor } },
        y: { stacked: true, ticks: { color: textColor, precision: 0 }, grid: { color: gridColor }, beginAtZero: true }
      },
      plugins: {
        legend: { labels: { color: textColor, font: { size: 11 } } }
      }
    }
  });
}

function renderCategoryChart(data) {
  destroyChart("categories");
  const ctx = document.getElementById("chartCategories")?.getContext("2d");
  if (!ctx) return;

  const textColor = getChartTextColor();
  const palette = ["#00E5FF", "#8B5CF6", "#3B82F6", "#F59E0B", "#EF4444", "#22C55E", "#EC4899", "#14B8A6"];

  chartInstances["categories"] = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: data.categories,
      datasets: [{
        data: data.counts,
        backgroundColor: palette.slice(0, data.categories.length),
        borderWidth: 1,
        borderColor: "rgba(11, 16, 32, 0.8)"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "right", labels: { color: textColor, boxWidth: 12, font: { size: 11 } } }
      },
      cutout: "65%"
    }
  });
}

function renderSeverityChart(data) {
  destroyChart("severity");
  const ctx = document.getElementById("chartSeverity")?.getContext("2d");
  if (!ctx) return;

  const textColor = getChartTextColor();
  const gridColor = getChartGridColor();

  chartInstances["severity"] = new Chart(ctx, {
    type: "bar",
    data: {
      labels: data.severities,
      datasets: [{
        label: "Incidents",
        data: data.counts,
        backgroundColor: ["#EF4444", "#F59E0B", "#3B82F6", "#22C55E"],
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: textColor }, grid: { display: false } },
        y: { ticks: { color: textColor, precision: 0 }, grid: { color: gridColor }, beginAtZero: true }
      }
    }
  });
}

function renderSourceChart(data) {
  destroyChart("sources");
  const ctx = document.getElementById("chartSources")?.getContext("2d");
  if (!ctx) return;

  const textColor = getChartTextColor();
  const gridColor = getChartGridColor();

  chartInstances["sources"] = new Chart(ctx, {
    type: "bar",
    data: {
      labels: data.sources,
      datasets: [{
        label: "Detections",
        data: data.counts,
        backgroundColor: "rgba(59, 130, 246, 0.8)",
        borderRadius: 4
      }]
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: textColor, precision: 0 }, grid: { color: gridColor }, beginAtZero: true },
        y: { ticks: { color: textColor }, grid: { display: false } }
      }
    }
  });
}

function renderHeatmap(data) {
  const container = document.getElementById("heatmapMatrixContainer");
  if (!container) return;

  const days = data.days;
  const hours = data.hours;
  const matrix = data.matrix;
  const maxVal = data.max_val || 1;

  let html = `<table class="heatmap-table">
    <thead>
      <tr>
        <th style="font-size: 0.75rem; color: var(--text-dim); text-align: left; padding: 4px;">Day / Hr</th>`;
  
  for (let h = 0; h < 24; h += 2) {
    html += `<th colspan="2" style="font-size: 0.7rem; color: var(--text-dim); text-align: center;">${h}:00</th>`;
  }
  html += `</tr></thead><tbody>`;

  days.forEach((day, dIdx) => {
    html += `<tr><td style="font-size: 0.78rem; font-weight: 600; color: var(--text-muted); padding: 4px 8px 4px 0;">${day.slice(0, 3)}</td>`;
    for (let h = 0; h < 24; h++) {
      const val = matrix[dIdx][h];
      const intensity = val > 0 ? Math.min(1, val / (maxVal > 0 ? maxVal : 1)) : 0;
      let bg = "rgba(148, 163, 184, 0.08)";
      let textColor = "transparent";

      if (val > 0) {
        bg = `rgba(0, 229, 255, ${0.2 + intensity * 0.75})`;
        textColor = intensity > 0.4 ? "#0B1020" : "#F8FAFC";
      }

      html += `<td>
        <div class="heatmap-cell" 
             style="background: ${bg}; color: ${textColor};" 
             title="${day} at ${h}:00 - ${val} incident(s)">
          ${val > 0 ? val : ""}
        </div>
      </td>`;
    }
    html += `</tr>`;
  });

  html += `</tbody></table>`;
  container.innerHTML = html;
}
