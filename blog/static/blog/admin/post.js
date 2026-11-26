(() => {
  const init = () => {
    const title = document.getElementById('id_title');
    const slug = document.getElementById('id_slug');
    if (!title || !slug) return;
    title.addEventListener('input', () => {
      slug.value = window.URLify(title.value, 240, false);
      slug.dispatchEvent(new Event('change', {bubbles: true}));
    });
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
