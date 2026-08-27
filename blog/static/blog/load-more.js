document.addEventListener("DOMContentLoaded", () => {
  const list = document.querySelector("[data-post-list]");
  const button = document.querySelector("[data-load-more]");
  const status = document.querySelector("[data-load-status]");
  if (!list || !button) return;

  button.addEventListener("click", async (event) => {
    event.preventDefault();
    const nextPage = button.dataset.nextPage;
    if (!nextPage || button.getAttribute("aria-busy") === "true") return;

    button.setAttribute("aria-busy", "true");
    button.textContent = "Memuat…";
    if (status) status.textContent = "Sedang memuat tulisan berikutnya.";

    try {
      const response = await fetch(`?page=${encodeURIComponent(nextPage)}`, {
        headers: {"X-Requested-With": "XMLHttpRequest"},
      });
      if (!response.ok) throw new Error("Gagal memuat tulisan");
      list.insertAdjacentHTML("beforeend", await response.text());
      const followingPage = response.headers.get("X-Next-Page");
      if (followingPage) {
        button.dataset.nextPage = followingPage;
        button.href = `?page=${followingPage}`;
        button.textContent = "Muat lebih banyak";
        button.removeAttribute("aria-busy");
        if (status) status.textContent = "Tulisan berikutnya berhasil dimuat.";
      } else {
        button.closest(".load-more-wrap").remove();
      }
    } catch (_error) {
      button.textContent = "Coba lagi";
      button.removeAttribute("aria-busy");
      if (status) status.textContent = "Tulisan belum berhasil dimuat. Silakan coba lagi.";
    }
  });
});
