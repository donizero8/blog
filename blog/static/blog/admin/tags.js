document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-tag-editor]").forEach((editor) => {
    const hidden = editor.querySelector("[data-tag-value]");
    const entry = editor.querySelector("[data-tag-entry]");
    const chips = editor.querySelector("[data-tag-chips]");
    let tags = hidden.value.split(",").map((tag) => tag.trim()).filter(Boolean);

    const sync = () => { hidden.value = tags.join(", "); };
    const render = () => {
      chips.replaceChildren();
      tags.forEach((tag, index) => {
        const chip = document.createElement("span");
        chip.className = "tag-chip";
        chip.append(document.createTextNode(tag));
        const remove = document.createElement("button");
        remove.type = "button";
        remove.setAttribute("aria-label", `Hapus tag ${tag}`);
        remove.textContent = "×";
        remove.addEventListener("click", () => { tags.splice(index, 1); sync(); render(); entry.focus(); });
        chip.append(remove);
        chips.append(chip);
      });
      sync();
    };
    const add = () => {
      const tag = entry.value.trim().replace(/\s+/g, " ").slice(0, 60);
      if (tag && !tags.some((item) => item.toLowerCase() === tag.toLowerCase()) && tags.length < 12) tags.push(tag);
      entry.value = "";
      render();
    };
    entry.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === ",") { event.preventDefault(); add(); }
      if (event.key === "Backspace" && !entry.value && tags.length) { tags.pop(); render(); }
    });
    entry.addEventListener("change", add);
    editor.closest("form")?.addEventListener("submit", () => { if (entry.value.trim()) add(); sync(); });
    render();
  });
});
