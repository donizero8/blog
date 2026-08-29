(function () {
  "use strict";

  const storageKey = "ruang-tulis-theme";
  const media = window.matchMedia("(prefers-color-scheme: dark)");

  function storedTheme() {
    try {
      const value = window.localStorage.getItem(storageKey);
      return value === "light" || value === "dark" ? value : null;
    } catch (_error) {
      return null;
    }
  }

  function resolvedTheme() {
    return storedTheme() || (media.matches ? "dark" : "light");
  }

  function updateControls(theme) {
    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
      const dark = theme === "dark";
      button.setAttribute("aria-pressed", String(dark));
      button.setAttribute("aria-label", dark ? "Switch to light mode" : "Switch to dark mode");
      button.title = dark ? "Switch to light mode" : "Switch to dark mode";
      const icon = button.querySelector("[data-theme-icon]");
      const label = button.querySelector("[data-theme-label]");
      if (icon) icon.textContent = dark ? "☀" : "☾";
      if (label) label.textContent = dark ? "Light mode" : "Dark mode";
    });
  }

  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    updateControls(theme);
  }

  applyTheme(resolvedTheme());

  document.addEventListener("DOMContentLoaded", () => {
    applyTheme(resolvedTheme());
    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
      button.addEventListener("click", () => {
        const nextTheme = resolvedTheme() === "dark" ? "light" : "dark";
        try { window.localStorage.setItem(storageKey, nextTheme); } catch (_error) { /* Theme still applies for this page. */ }
        applyTheme(nextTheme);
      });
    });
  });

  media.addEventListener("change", () => {
    if (!storedTheme()) applyTheme(resolvedTheme());
  });
})();
