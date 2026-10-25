// CyberShield AI Interactive Visualization Studio
let studioChartInstance = null;
let currentChartData = null;

document.addEventListener("DOMContentLoaded", () => {
  initStudioEvents();
  generateStudioChart();
});

function initStudioEvents() {
  document.getElementById("btnGenerateChart")?.addEventListener("click", generateStudioChart);

  document.getElementById("chartTypeSelect")?.addEventListener("change", handleChartTypeChange);

  document.getElementById("btnDownloadChartPng")?.addEventListener("click", () => {
    if (!studioChartInstance) return;
    const url = studioChartInstance.toBase64Image();
    const a = document.createElement("a");
    a.href = url;
    a.download = `cybershield_chart_${Date.now()}.png`;
    a.click();
    showToast("Chart exported as PNG", "success");
  });

  document.getElementById("btnExportChartCsv")?.addEventListener("click", () => {
    if (!currentChartData || !currentChartData.labels) return;
    let csv = "Label,Value\n";
    currentChartData.labels.forEach((lbl, idx) => {
      const val = currentChartData.values[idx] !== undefined ? currentChartData.values[idx] : "";
      csv += `"${lbl}",${val}\n`;
    });
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `cybershield_chart_data_${Date.now()}.csv`;
    a.click();
    showToast("Underlying chart data exported as CSV", "success");
  });
}

function handleChartTypeChange() {
  const chartType = document.getElementById("chartTypeSelect").value;
  const yAxisContainer = document.getElementById("yAxisFieldContainer");
  if (chartType === "scatter" || chartType === "correlation") {
    yAxisContainer.classList.remove("d-none");
  } else {
    yAxisContainer.classList.add("d-none");
  }
}

async function generateStudioChart() {
  const chartType = document.getElementById("chartTypeSelect").value;
  const xAxis = document.getElementById("xAxisField").value;
  const yAxis = document.getElementById("yAxisField")?.value || "resolution_time";
  const customTitle = document.getElementById("chartCustomTitle").value || "Cyber Threat Visualization";
  const sevFilter = document.getElementById("studioFilterSeverity").value;

  const statusContainer = document.getElementById("chartStatusMsg");
  statusContainer.classList.add("d-none");

  // Fetch data
  const params = new URLSearchParams();
  if (sevFilter && sevFilter !== "all") params.append("severity", sevFilter);

  try {
    const res = await fetch(`/api/incidents?per_page=500&${params.toString()}`);
    const json = await res.json();

    if (!json.success || !json.data.items || json.data.items.length === 0) {
      statusContainer.className = "alert alert-warning";
      statusContainer.innerText = "No incident records available to plot for the selected filters.";
      statusContainer.classList.remove("d-none");
      return;
    }

    const items = json.data.items;
    renderStudioChart(chartType, xAxis, yAxis, customTitle, items);

  } catch (err) {
    statusContainer.className = "alert alert-danger";
    statusContainer.innerText = "Error generating visualization data.";
    statusContainer.classList.remove("d-none");
  }
}

function renderStudioChart(type, xField, yField, title, items) {
  if (studioChartInstance) {
    studioChartInstance.destroy();
  }

  const canvas = document.getElementById("studioChartCanvas");
  const ctx = canvas.getContext("2d");
  const isLight = document.documentElement.getAttribute("data-theme") === "light";
  const textColor = isLight ? "#475569" : "#94a3b8";
  const gridColor = isLight ? "rgba(203, 213, 225, 0.4)" : "rgba(148, 163, 184, 0.1)";

  // Aggregate data by X field
  let labels = [];
  let values = [];

  if (type === "scatter") {
    // Scatter plot: numeric X and Y
    const scatterData = items
      .filter(i => i.resolution_time !== null && i.resolution_time !== undefined)
      .map(i => ({
        x: parseFloat(i.resolution_time) || 0,
        y: i.severity === "Critical" ? 4 : (i.severity === "High" ? 3 : (i.severity === "Medium" ? 2 : 1)),
        title: i.incident_id
      }));

    currentChartData = { labels: scatterData.map(d => d.title), values: scatterData.map(d => d.x) };

    studioChartInstance = new Chart(ctx, {
      type: "scatter",
      data: {
        datasets: [{
          label: "Incident Resolution vs Severity Tier (1=Low, 4=Crit)",
          data: scatterData,
          backgroundColor: "#00E5FF",
          borderColor: "#3B82F6",
          pointRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          title: { display: true, text: title, color: textColor, font: { size: 15, weight: "bold" } }
        },
        scales: {
          x: { title: { display: true, text: "Resolution Duration (Hours)", color: textColor }, ticks: { color: textColor }, grid: { color: gridColor } },
          y: { title: { display: true, text: "Severity Level (1-4)", color: textColor }, ticks: { color: textColor, stepSize: 1 }, grid: { color: gridColor } }
        }
      }
    });
    return;
  }

  // Grouped aggregation for categorical X fields
  const freqMap = {};
  items.forEach(i => {
    let key = i[xField] || "Unknown";
    if (xField === "incident_date") key = key.substring(0, 10);
    freqMap[key] = (freqMap[key] || 0) + 1;
  });

  labels = Object.keys(freqMap);
  values = Object.values(freqMap);
  currentChartData = { labels, values };

  const palette = [
    "#00E5FF", "#3B82F6", "#8B5CF6", "#EC4899",
    "#F59E0B", "#EF4444", "#22C55E", "#14B8A6",
    "#6366F1", "#D946EF", "#EAB308", "#06B6D4"
  ];

  let chartType = type;
  let isHorizontal = false;
  if (type === "horizontalBar") {
    chartType = "bar";
    isHorizontal = true;
  } else if (type === "area") {
    chartType = "line";
  }

  studioChartInstance = new Chart(ctx, {
    type: chartType,
    data: {
      labels: labels,
      datasets: [{
        label: "Frequency",
        data: values,
        backgroundColor: (type === "pie" || type === "doughnut") 
          ? palette.slice(0, labels.length) 
          : (type === "area" ? "rgba(0, 229, 255, 0.25)" : "rgba(0, 229, 255, 0.75)"),
        borderColor: "#00E5FF",
        borderWidth: (type === "pie" || type === "doughnut") ? 1 : 2,
        fill: type === "area",
        tension: 0.35,
        borderRadius: type === "bar" ? 5 : 0
      }]
    },
    options: {
      indexAxis: isHorizontal ? "y" : "x",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: { display: true, text: title, color: textColor, font: { size: 15, weight: "bold" } },
        legend: {
          display: (type === "pie" || type === "doughnut"),
          position: "right",
          labels: { color: textColor, font: { size: 11 } }
        }
      },
      scales: (type === "pie" || type === "doughnut") ? {} : {
        x: { ticks: { color: textColor }, grid: { color: gridColor } },
        y: { ticks: { color: textColor, precision: 0 }, grid: { color: gridColor }, beginAtZero: true }
      }
    }
  });
}
