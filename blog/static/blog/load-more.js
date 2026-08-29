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
    button.textContent = "Loading…";
    if (status) status.textContent = "Loading more posts.";

    try {
      const response = await fetch(`?page=${encodeURIComponent(nextPage)}`, {
        headers: {"X-Requested-With": "XMLHttpRequest"},
      });
      if (!response.ok) throw new Error("Failed to load posts");
      list.insertAdjacentHTML("beforeend", await response.text());
      const followingPage = response.headers.get("X-Next-Page");
      if (followingPage) {
        button.dataset.nextPage = followingPage;
        button.href = `?page=${followingPage}`;
        button.textContent = "Load more";
        button.removeAttribute("aria-busy");
        if (status) status.textContent = "More posts have been loaded.";
      } else {
        button.closest(".load-more-wrap").remove();
      }
    } catch (_error) {
      button.textContent = "Try again";
      button.removeAttribute("aria-busy");
      if (status) status.textContent = "Posts could not be loaded. Please try again.";
    }
  });
});
