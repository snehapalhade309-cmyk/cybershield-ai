// CyberShield AI Settings & Preferences Manager
document.addEventListener("DOMContentLoaded", () => {
  loadSavedSettings();
  initSettingsEvents();
});

function loadSavedSettings() {
  const theme = localStorage.getItem("cybershield_theme") || "dark";
  const pageSize = localStorage.getItem("cybershield_page_size") || "10";
  const apiKey = localStorage.getItem("cybershield_gemini_key") || "";

  const themeRadio = document.querySelector(`input[name="themeOption"][value="${theme}"]`);
  if (themeRadio) themeRadio.checked = true;

  const pageSizeSelect = document.getElementById("prefPageSize");
  if (pageSizeSelect) pageSizeSelect.value = pageSize;

  const apiKeyInput = document.getElementById("prefGeminiApiKey");
  if (apiKeyInput) apiKeyInput.value = apiKey;
}

function initSettingsEvents() {
  // Theme selector
  document.querySelectorAll('input[name="themeOption"]').forEach(radio => {
    radio.addEventListener("change", (e) => {
      const theme = e.target.value;
      document.documentElement.setAttribute("data-theme", theme);
      localStorage.setItem("cybershield_theme", theme);
      updateThemeIcon(theme);
      showToast(`Interface switched to ${theme} mode`, "info");
    });
  });

  // Save Preferences Form
  document.getElementById("formGeneralPreferences")?.addEventListener("submit", (e) => {
    e.preventDefault();
    const pageSize = document.getElementById("prefPageSize").value;
    const apiKey = document.getElementById("prefGeminiApiKey").value.trim();

    localStorage.setItem("cybershield_page_size", pageSize);
    localStorage.setItem("cybershield_gemini_key", apiKey);

    showToast("Preferences saved successfully", "success");
  });

  // Clear Demo Data
  document.getElementById("btnClearDemoData")?.addEventListener("click", () => {
    const modal = new bootstrap.Modal(document.getElementById("confirmClearDemoModal"));
    modal.show();
  });

  document.getElementById("btnConfirmClearDemo")?.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/settings/clear-demo", { method: "POST" });
      const json = await res.json();
      bootstrap.Modal.getInstance(document.getElementById("confirmClearDemoModal"))?.hide();

      if (json.success) {
        showToast(json.message, "success");
      } else {
        showToast(json.error || "Failed to clear demo records", "danger");
      }
    } catch (err) {
      showToast("Network error executing operation", "danger");
    }
  });

  // Reset Demo Data
  document.getElementById("btnResetDemoData")?.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/settings/reset-demo", { method: "POST" });
      const json = await res.json();
      if (json.success) {
        showToast(json.message, "success");
      } else {
        showToast(json.error || "Failed to refresh demo dataset", "danger");
      }
    } catch (err) {
      showToast("Network error executing operation", "danger");
    }
  });
}
