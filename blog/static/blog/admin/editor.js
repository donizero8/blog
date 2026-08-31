document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-medium-editor]").forEach((wrapper) => {
    wrapper.closest(".form-row")?.classList.add("has-medium-editor");
    const canvas = wrapper.querySelector(".medium-canvas");
    const textarea = wrapper.querySelector("textarea");
    const imageDialog = wrapper.querySelector("[data-image-dialog]");
    const imageControls = wrapper.querySelector("[data-image-controls]");
    let savedRange = null;
    let selectedImage = null;
    document.execCommand("defaultParagraphSeparator", false, "p");
    document.execCommand("styleWithCSS", false, false);

    function normalizedHtml() {
      const clone = canvas.cloneNode(true);
      clone.querySelectorAll("b, i").forEach((element) => {
        const semantic = document.createElement(element.tagName === "B" ? "strong" : "em");
        semantic.innerHTML = element.innerHTML;
        element.replaceWith(semantic);
      });
      clone.querySelectorAll("p > ul, p > ol").forEach((list) => {
        const paragraph = list.parentElement;
        paragraph.replaceWith(...paragraph.childNodes);
      });
      Array.from(clone.childNodes).forEach((child) => {
        if (child.nodeType === Node.TEXT_NODE && child.textContent.trim()) {
          const paragraph = document.createElement("p");
          child.replaceWith(paragraph);
          paragraph.appendChild(child);
        } else if (child.nodeType === Node.ELEMENT_NODE && child.tagName === "DIV") {
          const paragraph = document.createElement("p");
          paragraph.innerHTML = child.innerHTML || "<br>";
          child.replaceWith(paragraph);
        }
      });
      return clone.innerHTML;
    }

    const sync = () => { textarea.value = normalizedHtml(); };
    if (!canvas.innerHTML.trim()) canvas.innerHTML = "<p><br></p>";
    canvas.addEventListener("input", sync);
    canvas.addEventListener("blur", sync);

    function rememberSelection() {
      const selection = window.getSelection();
      if (selection?.rangeCount && canvas.contains(selection.anchorNode)) {
        savedRange = selection.getRangeAt(0).cloneRange();
      }
    }

    function selectionElement() {
      const selection = window.getSelection();
      if (!selection?.rangeCount || !canvas.contains(selection.anchorNode)) return null;
      return selection.anchorNode.nodeType === Node.ELEMENT_NODE
        ? selection.anchorNode
        : selection.anchorNode.parentElement;
    }

    function setActive(button, active) {
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", String(active));
    }

    function updateToolbar() {
      const node = selectionElement();
      if (!node) return;
      wrapper.querySelectorAll(".medium-toolbar button").forEach((button) => {
        let active = false;
        if (button.dataset.block) {
          const block = node.closest("p, h2, h3, blockquote, pre, li, div");
          active = block?.tagName.toLowerCase() === button.dataset.block;
          if (button.dataset.block === "p" && (
            !block || block === canvas || block.tagName === "DIV"
          )) active = true;
        } else if (button.hasAttribute("data-code")) {
          active = Boolean(node.closest("pre"));
        } else if (button.dataset.command === "bold") {
          active = document.queryCommandState("bold") || Boolean(node.closest("strong, b"));
        } else if (button.dataset.command === "italic") {
          active = document.queryCommandState("italic") || Boolean(node.closest("em, i"));
        } else if (button.dataset.command === "createLink") {
          active = Boolean(node.closest("a"));
        } else if (button.dataset.value === "blockquote") {
          active = Boolean(node.closest("blockquote"));
        } else if (button.dataset.command === "insertUnorderedList") {
          active = Boolean(node.closest("ul"));
        }
        setActive(button, active);
      });
    }

    wrapper.querySelectorAll(".medium-toolbar button").forEach((button) => {
      button.setAttribute("aria-pressed", "false");
    });
    document.addEventListener("selectionchange", () => {
      rememberSelection();
      updateToolbar();
    });
    canvas.addEventListener("keyup", updateToolbar);
    canvas.addEventListener("mouseup", updateToolbar);
    canvas.addEventListener("input", updateToolbar);

    wrapper.querySelectorAll("[data-command]").forEach((button) => {
      button.addEventListener("mousedown", (event) => {
        event.preventDefault();
        let value = button.dataset.value || null;
        if (button.dataset.command === "createLink") {
          value = window.prompt("Alamat tautan (https://…)");
          if (!value) return;
        }
        document.execCommand(button.dataset.command, false, value);
        sync();
        updateToolbar();
      });
    });
    wrapper.querySelectorAll("[data-block]").forEach((button) => {
      button.addEventListener("mousedown", (event) => {
        event.preventDefault();
        if (button.dataset.block === "p" && currentCodeBlock()) {
          exitCodeBlock();
          return;
        }
        document.execCommand("formatBlock", false, button.dataset.block);
        sync();
        updateToolbar();
      });
    });

    function currentCodeBlock() {
      const selection = window.getSelection();
      if (!selection?.rangeCount || !canvas.contains(selection.anchorNode)) return null;
      const node = selection.anchorNode.nodeType === Node.ELEMENT_NODE
        ? selection.anchorNode
        : selection.anchorNode.parentElement;
      return node?.closest("pre") || null;
    }

    function exitCodeBlock() {
      const pre = currentCodeBlock();
      if (!pre) return false;
      const paragraph = document.createElement("p");
      paragraph.appendChild(document.createElement("br"));
      pre.after(paragraph);
      const range = document.createRange();
      range.setStart(paragraph, 0);
      range.collapse(true);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      canvas.focus();
      sync();
      updateToolbar();
      return true;
    }

    const toggleCode = () => {
      if (!exitCodeBlock()) document.execCommand("formatBlock", false, "pre");
      sync();
      updateToolbar();
    };
    wrapper.querySelector("[data-code]").addEventListener("mousedown", (event) => {
      event.preventDefault();
      toggleCode();
    });
    canvas.addEventListener("keydown", (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
        event.preventDefault();
        toggleCode();
        return;
      }
      const pre = currentCodeBlock();
      if (pre && event.key === "Escape") {
        event.preventDefault();
        exitCodeBlock();
        return;
      }
      if (pre && event.key === "Enter" && pre.textContent.endsWith("\n")) {
        event.preventDefault();
        pre.textContent = pre.textContent.slice(0, -1);
        exitCodeBlock();
      }
    });

    function selectImage(image) {
      selectedImage = image;
      imageControls.hidden = !image;
      imageControls.querySelectorAll("[data-image-size]").forEach((button) => {
        setActive(button, Boolean(image?.classList.contains(`image-${button.dataset.imageSize}`)));
      });
    }

    canvas.addEventListener("click", (event) => {
      selectImage(event.target.closest("img.article-image"));
    });
    wrapper.querySelectorAll("[data-image-size]").forEach((button) => {
      button.addEventListener("mousedown", (event) => {
        event.preventDefault();
        if (!selectedImage) return;
        selectedImage.classList.remove("image-small", "image-medium", "image-large");
        selectedImage.classList.add(`image-${button.dataset.imageSize}`);
        sync();
        selectImage(selectedImage);
      });
    });
    wrapper.querySelector("[data-image-remove]").addEventListener("mousedown", (event) => {
      event.preventDefault();
      if (!selectedImage) return;
      selectedImage.remove();
      selectImage(null);
      sync();
    });

    wrapper.querySelector("[data-image]").addEventListener("mousedown", (event) => {
      event.preventDefault();
      rememberSelection();
      imageDialog.querySelector("[data-image-file]").value = "";
      imageDialog.querySelector("[data-image-url]").value = "";
      imageDialog.querySelector("[data-image-alt]").value = "";
      imageDialog.querySelector("[data-image-initial-size]").value = "medium";
      imageDialog.querySelector("[data-image-status]").textContent = "";
      imageDialog.showModal();
    });
    imageDialog.querySelectorAll("[data-image-cancel]").forEach((button) => {
      button.addEventListener("click", () => imageDialog.close());
    });
    imageDialog.querySelector("[data-image-file]").addEventListener("change", (event) => {
      if (event.target.files.length) imageDialog.querySelector("[data-image-url]").value = "";
    });
    imageDialog.querySelector("[data-image-url]").addEventListener("input", (event) => {
      if (event.target.value.trim()) imageDialog.querySelector("[data-image-file]").value = "";
    });

    function insertImage({src, width, height, external = false}) {
      const image = document.createElement("img");
      const size = imageDialog.querySelector("[data-image-initial-size]").value;
      image.src = src;
      image.alt = imageDialog.querySelector("[data-image-alt]").value.trim();
      image.className = `article-image image-${size}`;
      image.loading = "lazy";
      if (width) image.width = width;
      if (height) image.height = height;
      if (external) image.referrerPolicy = "no-referrer";

      const range = savedRange && canvas.contains(savedRange.commonAncestorContainer)
        ? savedRange
        : document.createRange();
      if (!savedRange || !canvas.contains(range.commonAncestorContainer)) {
        range.selectNodeContents(canvas);
        range.collapse(false);
      }
      range.deleteContents();
      range.insertNode(image);
      const paragraph = document.createElement("p");
      paragraph.appendChild(document.createElement("br"));
      image.after(paragraph);
      imageDialog.close();
      canvas.focus();
      selectImage(image);
      sync();
    }

    imageDialog.querySelector("[data-image-upload]").addEventListener("click", async () => {
      const fileInput = imageDialog.querySelector("[data-image-file]");
      const urlInput = imageDialog.querySelector("[data-image-url]");
      const status = imageDialog.querySelector("[data-image-status]");
      const uploadButton = imageDialog.querySelector("[data-image-upload]");
      const rawUrl = urlInput.value.trim();
      if (!fileInput.files.length && !rawUrl) {
        status.textContent = "Pilih file atau masukkan URL gambar.";
        return;
      }
      uploadButton.disabled = true;
      try {
        if (rawUrl) {
          const url = new URL(rawUrl);
          if (!['http:', 'https:'].includes(url.protocol)) {
            throw new Error("URL gambar harus menggunakan http:// atau https://.");
          }
          insertImage({src: url.href, external: true});
          return;
        }

        const data = new FormData();
        data.append("image", fileInput.files[0]);
        status.textContent = "Mengompresi dan mengunggah…";
        const csrfToken = wrapper.closest("form")?.querySelector("[name=csrfmiddlewaretoken]")?.value;
        const response = await fetch(wrapper.querySelector("[data-image-upload-url]").dataset.imageUploadUrl, {
          method: "POST",
          headers: {"X-CSRFToken": csrfToken},
          body: data,
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "Gambar gagal diunggah.");
        insertImage({src: result.url, width: result.width, height: result.height});
      } catch (error) {
        status.textContent = error instanceof TypeError
          ? "URL gambar tidak valid."
          : error.message;
      } finally {
        uploadButton.disabled = false;
      }
    });
    wrapper.closest("form")?.addEventListener("submit", sync);
  });
});
