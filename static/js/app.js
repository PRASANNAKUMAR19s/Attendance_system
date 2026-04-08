/**
 * app.js — Main application logic
 * ================================
 * Shared utilities used across all pages.
 */

"use strict";

/* ── Auto-dismiss alerts after 5 s ───────────────────────────────────── */
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".alert.alert-dismissible").forEach(function (el) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });

  /* ── Confirm before delete forms ─────────────────────────────────── */
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (!confirm(form.dataset.confirm)) {
        e.preventDefault();
      }
    });
  });

  /* ── Drag-over visual feedback for drop zones ─────────────────────── */
  document.querySelectorAll("[id$='dropZone']").forEach(function (zone) {
    zone.addEventListener("dragover", function (e) {
      e.preventDefault();
      zone.classList.add("drag-over");
    });
    zone.addEventListener("dragleave", function () {
      zone.classList.remove("drag-over");
    });
    zone.addEventListener("drop", function (e) {
      e.preventDefault();
      zone.classList.remove("drag-over");
    });
  });
});

/**
 * Show a Bootstrap toast notification.
 * @param {string} message
 * @param {'success'|'danger'|'warning'|'info'} type
 */
function showToast(message, type) {
  type = type || "info";
  const container = document.getElementById("toastContainer") ||
    (function () {
      const el = document.createElement("div");
      el.id = "toastContainer";
      el.className = "toast-container position-fixed bottom-0 end-0 p-3";
      el.style.zIndex = "1100";
      document.body.appendChild(el);
      return el;
    })();

  const id = "toast-" + Date.now();
  const toastEl = document.createElement("div");
  toastEl.id = id;
  toastEl.className = "toast align-items-center text-bg-" + type + " border-0";
  toastEl.setAttribute("role", "alert");

  const inner = document.createElement("div");
  inner.className = "d-flex";

  const body = document.createElement("div");
  body.className = "toast-body";
  body.textContent = message;   // use textContent to prevent XSS

  const closeBtn = document.createElement("button");
  closeBtn.type = "button";
  closeBtn.className = "btn-close btn-close-white me-2 m-auto";
  closeBtn.setAttribute("data-bs-dismiss", "toast");

  inner.appendChild(body);
  inner.appendChild(closeBtn);
  toastEl.appendChild(inner);
  container.appendChild(toastEl);
  const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
  toast.show();
  toastEl.addEventListener("hidden.bs.toast", function () { toastEl.remove(); });
}
