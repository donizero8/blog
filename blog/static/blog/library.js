document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-show-more]").forEach((button) => {
    const list = document.getElementById(button.getAttribute("aria-controls"));
    if (!list) return;
    const pageSize = Number.parseInt(list.dataset.pageSize, 10) || 4;

    button.addEventListener("click", () => {
      const hiddenItems = Array.from(list.children).filter((item) => item.hidden);
      hiddenItems.slice(0, pageSize).forEach((item) => { item.hidden = false; });
      if (hiddenItems.length <= pageSize) button.remove();
    });
  });
});
