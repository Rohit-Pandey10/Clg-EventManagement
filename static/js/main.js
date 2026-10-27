/**
 * CEMS Frontend Controller
 * Password toggle, user menu dropdown, mobile nav, and alert dismissal.
 */

document.addEventListener("DOMContentLoaded", function () {
  initPasswordToggle();
  initMessageDismiss();
  initUserDropdown();
  initMobileNav();
  initHeaderScroll();
});

function initPasswordToggle() {
  const toggleBtn = document.getElementById("toggle-password-btn");
  const passwordInput = document.getElementById("login-password") || document.querySelector("input[name='password']");

  if (toggleBtn && passwordInput) {
    toggleBtn.addEventListener("click", function () {
      const isPassword = passwordInput.type === "password";
      passwordInput.type = isPassword ? "text" : "password";
      toggleBtn.textContent = isPassword ? "Hide" : "Show";
    });
  }
}

function initMessageDismiss() {
  document.addEventListener("click", function (e) {
    const closeBtn = e.target.closest(".alert-close");
    if (closeBtn) {
      const alert = closeBtn.closest(".cems-alert");
      if (alert) {
        alert.remove();
      }
    }
  });
}

function initUserDropdown() {
  const trigger = document.getElementById("user-menu-trigger");
  const menu = document.getElementById("user-menu-dropdown");

  if (!trigger || !menu) return;

  trigger.addEventListener("click", function (e) {
    e.stopPropagation();
    const isOpen = !menu.classList.contains("hidden");
    if (isOpen) {
      menu.classList.add("hidden");
      trigger.setAttribute("aria-expanded", "false");
    } else {
      menu.classList.remove("hidden");
      trigger.setAttribute("aria-expanded", "true");
    }
  });

  document.addEventListener("click", function (e) {
    if (!menu.contains(e.target) && e.target !== trigger) {
      menu.classList.add("hidden");
      trigger.setAttribute("aria-expanded", "false");
    }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !menu.classList.contains("hidden")) {
      menu.classList.add("hidden");
      trigger.setAttribute("aria-expanded", "false");
      trigger.focus();
    }
  });
}

function initMobileNav() {
  const toggleBtn = document.getElementById("mobile-menu-btn");
  const mobileMenu = document.getElementById("mobile-menu");
  if (toggleBtn && mobileMenu) {
    toggleBtn.addEventListener("click", function () {
      mobileMenu.classList.toggle("hidden");
    });
  }
}

function initHeaderScroll() {
  const header = document.querySelector("header");
  if (!header) return;

  window.addEventListener("scroll", function () {
    if (window.scrollY > 8) {
      header.classList.add("shadow-[0_1px_2px_rgba(0,0,0,0.04)]");
    } else {
      header.classList.remove("shadow-[0_1px_2px_rgba(0,0,0,0.04)]");
    }
  }, { passive: true });
}

