(() => {
  "use strict";

  const initialize = () => {
    const status = document.getElementById("id_status");
    const progressSection = document.querySelector("fieldset.book-progress-section");

    if (!status || !progressSection) return;

    const updateProgressVisibility = () => {
      const isWantToRead = status.value === "want";
      progressSection.hidden = isWantToRead;
      progressSection.setAttribute("aria-hidden", String(isWantToRead));
    };

    status.addEventListener("change", updateProgressVisibility);
    updateProgressVisibility();
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize, { once: true });
  } else {
    initialize();
  }
})();
