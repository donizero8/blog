(() => {
  "use strict";

  function initialize(picker) {
    const buttons = [...picker.querySelectorAll("[data-cover-method]")];
    const panels = [...picker.querySelectorAll("[data-cover-panel]")];
    const upload = picker.querySelector("[data-cover-upload]");
    const url = picker.querySelector("[data-cover-url]");
    const hiddenUrl = document.getElementById("id_cover_url");

    function select(method) {
      buttons.forEach(button => button.setAttribute("aria-pressed", String(button.dataset.coverMethod === method)));
      panels.forEach(panel => { panel.hidden = panel.dataset.coverPanel !== method; });
      if (method === "upload") {
        url.value = "";
        if (hiddenUrl) hiddenUrl.value = "";
      } else {
        upload.value = "";
      }
    }

    if (hiddenUrl?.value) {
      url.value = hiddenUrl.value;
      select("url");
    } else {
      select("upload");
    }
    buttons.forEach(button => button.addEventListener("click", () => select(button.dataset.coverMethod)));
    url.addEventListener("input", () => { if (hiddenUrl) hiddenUrl.value = url.value; });
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-book-cover-picker]").forEach(initialize);
  });
})();
