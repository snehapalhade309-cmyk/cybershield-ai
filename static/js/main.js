// CyberShield AI Core UI & Shared Utilities
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initClock();
  initSidebarMobile();
  initGlobalSearch();
});

// Theme Management
function initTheme() {
  const savedTheme = localStorage.getItem("cybershield_theme") || "dark";
  document.documentElement.setAttribute("data-theme", savedTheme);
  updateThemeIcon(savedTheme);

  const toggleBtn = document.getElementById("themeToggleBtn");
  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme") || "dark";
      const next = current === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("cybershield_theme", next);
      updateThemeIcon(next);
      window.dispatchEvent(new CustomEvent("themeChanged", { detail: { theme: next } }));
    });
  }
}

function updateThemeIcon(theme) {
  const icon = document.querySelector("#themeToggleBtn i");
  if (icon) {
    if (theme === "light") {
      icon.className = "fas fa-moon";
    } else {
      icon.className = "fas fa-sun";
    }
  }
}

// Live Clock in UTC & Local
function initClock() {
  const clockEl = document.getElementById("topbarClock");
  if (!clockEl) return;
  const update = () => {
    const now = new Date();
    clockEl.innerText = now.toLocaleDateString("en-US", {
      month: "short", day: "numeric", year: "numeric",
      hour: "2-digit", minute: "2-digit", second: "2-digit"
    });
  };
  update();
  setInterval(update, 1000);
}

// Mobile Sidebar Drawer
function initSidebarMobile() {
  const toggle = document.getElementById("sidebarToggleBtn");
  const sidebar = document.getElementById("cyberSidebar");
  if (toggle && sidebar) {
    toggle.addEventListener("click", () => {
      sidebar.classList.toggle("show");
    });
    // Close sidebar on outer click on mobile
    document.addEventListener("click", (e) => {
      if (window.innerWidth < 992 && sidebar.classList.contains("show")) {
        if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
          sidebar.classList.remove("show");
        }
      }
    });
  }
}

// Global Incident Search
function initGlobalSearch() {
  const searchInput = document.getElementById("globalSearchInput");
  if (!searchInput) return;
  searchInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      const q = encodeURIComponent(searchInput.value.trim());
      if (q) {
        window.location.href = `/incidents?search=${q}`;
      }
    }
  });
}

// Toast Notifications
function showToast(message, type = "info") {
  let toastContainer = document.getElementById("toastContainer");
  if (!toastContainer) {
    toastContainer = document.createElement("div");
    toastContainer.id = "toastContainer";
    toastContainer.style.position = "fixed";
    toastContainer.style.bottom = "20px";
    toastContainer.style.right = "20px";
    toastContainer.style.zIndex = "9999";
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement("div");
  toast.className = `glass-panel p-3 mb-2 d-flex align-items-center gap-2 border-${type}`;
  toast.style.minWidth = "280px";
  toast.style.boxShadow = "0 8px 24px rgba(0,0,0,0.4)";

  let icon = "info-circle";
  if (type === "success") icon = "check-circle text-success";
  else if (type === "danger" || type === "error") icon = "exclamation-triangle text-danger";
  else if (type === "warning") icon = "bell text-warning";
  else icon = "info-circle text-info";

  toast.innerHTML = `
    <i class="fas fa-${icon} fs-5"></i>
    <div class="flex-grow-1" style="font-size: 0.9rem;">${message}</div>
    <button type="button" class="btn-close btn-close-white" style="font-size: 0.75rem;"></button>
  `;

  toast.querySelector(".btn-close").addEventListener("click", () => toast.remove());
  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transition = "opacity 0.5s ease";
    setTimeout(() => toast.remove(), 500);
  }, 4000);
}
