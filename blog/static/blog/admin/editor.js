document.addEventListener("DOMContentLoaded", () => {
  function initializeEditor(wrapper) {
    if (wrapper.dataset.editorInitialized === "true") return;
    wrapper.dataset.editorInitialized = "true";
    wrapper.closest(".form-row")?.classList.add("has-medium-editor");
    const canvas = wrapper.querySelector(".medium-canvas");
    const textarea = wrapper.querySelector("textarea");
    const imageDialog = wrapper.querySelector("[data-image-dialog]");
    const imageControls = wrapper.querySelector("[data-image-controls]");
    const emojiToggle = wrapper.querySelector("[data-emoji-toggle]");
    const emojiPicker = wrapper.querySelector("[data-emoji-picker]");
    const draftStatus = wrapper.querySelector("[data-draft-status]");
    const baselineHtml = textarea.value;
    const draftKey = `dony-notebook:editor-draft:${window.location.pathname}:${textarea.name}`;
    const localDraftEnabled = !/^\/admin\/blog\/post\/add\/?$/.test(window.location.pathname);
    let savedRange = null;
    let selectedImage = null;
    let draftTimer = null;
    let draftReady = false;
    document.execCommand("defaultParagraphSeparator", false, "p");
    document.execCommand("styleWithCSS", false, false);

    function normalizedHtml() {
      const clone = canvas.cloneNode(true);
      clone.querySelectorAll("[data-video-block]").forEach((block) => {
        const frame = block.querySelector("iframe.youtube-embed");
        if (frame) block.replaceWith(frame);
        else block.remove();
      });
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

    function setDraftStatus(message, warning = false) {
      draftStatus.textContent = message;
      draftStatus.classList.toggle("is-warning", warning);
    }

    function persistLocalDraft() {
      if (!draftReady || !localDraftEnabled) return;
      window.clearTimeout(draftTimer);
      const html = normalizedHtml();
      textarea.value = html;
      try {
        if (html === baselineHtml) {
          window.localStorage.removeItem(draftKey);
          setDraftStatus("Tidak ada perubahan lokal yang belum disimpan.");
          return;
        }
        window.localStorage.setItem(draftKey, JSON.stringify({html, updatedAt: Date.now()}));
        const time = new Intl.DateTimeFormat("id-ID", {hour: "2-digit", minute: "2-digit"}).format(new Date());
        setDraftStatus(`Draft lokal tersimpan pada ${time}.`);
      } catch (error) {
        setDraftStatus("Draft tidak dapat disimpan di browser ini.", true);
      }
    }

    function scheduleLocalDraft() {
      window.clearTimeout(draftTimer);
      draftTimer = window.setTimeout(persistLocalDraft, 500);
    }

    const sync = () => {
      textarea.value = normalizedHtml();
      if (draftReady) scheduleLocalDraft();
    };
    if (!canvas.innerHTML.trim()) canvas.innerHTML = "<p><br></p>";
    try {
      if (!localDraftEnabled) {
        window.localStorage.removeItem(draftKey);
        setDraftStatus("Artikel baru selalu dimulai kosong; draft lokal tidak digunakan.");
      }
      const savedDraft = JSON.parse(window.localStorage.getItem(draftKey) || "null");
      if (localDraftEnabled && savedDraft?.html && savedDraft.html !== baselineHtml) {
        const draftTemplate = document.createElement("template");
        draftTemplate.innerHTML = savedDraft.html;
        draftTemplate.content.querySelectorAll("iframe.youtube-embed").forEach((frame) => {
          frame.setAttribute("referrerpolicy", "strict-origin-when-cross-origin");
        });
        canvas.innerHTML = draftTemplate.innerHTML;
        textarea.value = savedDraft.html;
        setDraftStatus("Draft lokal dipulihkan. Perubahan Anda belum disimpan ke server.");
      } else if (localDraftEnabled && savedDraft) {
        window.localStorage.removeItem(draftKey);
      }
    } catch (error) {
      try { window.localStorage.removeItem(draftKey); } catch (storageError) { /* unavailable */ }
      setDraftStatus("Draft lokal yang rusak telah diabaikan.", true);
    }
    function enhanceVideos() {
      canvas.querySelectorAll("iframe.youtube-embed").forEach((frame) => {
        if (frame.closest("[data-video-block]")) return;
        const block = document.createElement("div");
        block.dataset.videoBlock = "";
        block.className = "medium-video-block";
        block.contentEditable = "false";
        const controls = document.createElement("div");
        controls.className = "medium-video-actions";
        for (const [action, label] of [["after", "Tulis setelah video"], ["remove", "Hapus video"]]) {
          const button = document.createElement("button");
          button.type = "button";
          button.dataset.videoAction = action;
          button.textContent = label;
          controls.appendChild(button);
        }
        frame.before(block);
        block.append(controls, frame);
      });
    }
    canvas.addEventListener("click", (event) => {
      const button = event.target.closest("[data-video-action]");
      if (!button) return;
      event.preventDefault();
      const block = button.closest("[data-video-block]");
      let paragraph = block.nextElementSibling;
      if (!paragraph || paragraph.tagName !== "P") {
        paragraph = document.createElement("p");
        paragraph.appendChild(document.createElement("br"));
        block.after(paragraph);
      }
      if (button.dataset.videoAction === "remove") block.remove();
      canvas.focus();
      const range = document.createRange();
      range.selectNodeContents(paragraph);
      range.collapse(true);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      rememberSelection();
      sync();
      updateToolbar();
    });
    enhanceVideos();
    new MutationObserver(enhanceVideos).observe(canvas, {childList: true, subtree: true});
    draftReady = true;
    canvas.addEventListener("input", sync);
    canvas.addEventListener("blur", sync);
    window.addEventListener("pagehide", persistLocalDraft);

    function rememberSelection() {
      const selection = window.getSelection();
      if (selection?.rangeCount && canvas.contains(selection.anchorNode)) {
        savedRange = selection.getRangeAt(0).cloneRange();
      }
    }

    function restoreSelection() {
      if (!savedRange || !canvas.contains(savedRange.commonAncestorContainer)) return false;
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(savedRange);
      return true;
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
      wrapper.querySelectorAll(".medium-toolbar > button, [data-emoji-toggle]").forEach((button) => {
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
          active = document.queryCommandState("bold");
        } else if (button.dataset.command === "italic") {
          active = document.queryCommandState("italic");
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

    wrapper.querySelectorAll(".medium-toolbar > button, [data-emoji-toggle]").forEach((button) => {
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
        if (
          button.dataset.command === "formatBlock"
          && button.dataset.value === "blockquote"
          && selectionElement()?.closest("blockquote")
        ) {
          value = "p";
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

    const youtubeButton = wrapper.querySelector("[data-youtube]");
    const youtubeDialog = wrapper.querySelector("[data-youtube-dialog]");
    const youtubeInput = youtubeDialog.querySelector("[data-youtube-html]");
    const youtubeStatus = youtubeDialog.querySelector("[data-youtube-status]");
    youtubeButton.addEventListener("mousedown", (event) => {
      event.preventDefault();
      rememberSelection();
    });
    youtubeButton.addEventListener("click", () => {
      rememberSelection();
      youtubeInput.value = "";
      youtubeStatus.textContent = "";
      youtubeDialog.showModal();
      youtubeInput.focus();
    });
    youtubeDialog.querySelectorAll("[data-youtube-cancel]").forEach((button) => {
      button.addEventListener("click", () => youtubeDialog.close());
    });
    youtubeInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
        event.preventDefault();
        youtubeDialog.querySelector("[data-youtube-insert]").click();
      }
    });
    youtubeDialog.querySelector("[data-youtube-insert]").addEventListener("click", () => {
      const value = youtubeInput.value;
      let id;
      try {
        // Parse in an inert template; never insert the supplied HTML into the page.
        const template = document.createElement("template");
        template.innerHTML = value.trim();
        const frames = template.content.querySelectorAll("iframe");
        if (frames.length !== 1) throw new Error();
        const url = new URL(frames[0].getAttribute("src"));
        if (url.protocol !== "https:" || url.username || url.password || url.port) throw new Error();
        if (!["youtube.com", "www.youtube.com", "youtube-nocookie.com", "www.youtube-nocookie.com"].includes(url.hostname)) throw new Error();
        id = url.pathname.match(/^\/embed\/([A-Za-z0-9_-]{11})\/?$/)?.[1];
        if (!/^[A-Za-z0-9_-]{11}$/.test(id || "")) throw new Error();
      } catch {
        youtubeStatus.textContent = "Kode embed tidak valid. Tempel HTML iframe untuk satu video YouTube, bukan URL.";
        youtubeInput.focus();
        return;
      }
      youtubeDialog.close();
      canvas.focus();
      if (!restoreSelection()) {
        const range = document.createRange();
        range.selectNodeContents(canvas);
        range.collapse(false);
        window.getSelection().removeAllRanges();
        window.getSelection().addRange(range);
      }
      document.execCommand("insertHTML", false, `<iframe class="youtube-embed" src="https://www.youtube-nocookie.com/embed/${id}" title="Video YouTube" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe><p><br></p>`);
      rememberSelection();
      sync();
      updateToolbar();
    });

    function closeEmojiPicker() {
      emojiPicker.hidden = true;
      emojiToggle.setAttribute("aria-expanded", "false");
    }

    emojiToggle.addEventListener("mousedown", (event) => {
      event.preventDefault();
      rememberSelection();
      emojiPicker.hidden = !emojiPicker.hidden;
      emojiToggle.setAttribute("aria-expanded", String(!emojiPicker.hidden));
    });
    emojiPicker.querySelectorAll("[data-emoji]").forEach((button) => {
      button.addEventListener("mousedown", (event) => {
        event.preventDefault();
        restoreSelection();
        canvas.focus();
        document.execCommand("insertText", false, button.dataset.emoji);
        rememberSelection();
        closeEmojiPicker();
        sync();
        updateToolbar();
      });
    });
    document.addEventListener("mousedown", (event) => {
      if (!event.target.closest(".medium-emoji-menu")) closeEmojiPicker();
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
      if (event.key === "Escape" && !emojiPicker.hidden) {
        event.preventDefault();
        closeEmojiPicker();
        return;
      }
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
    wrapper.closest("form")?.addEventListener("submit", () => {
      sync();
      persistLocalDraft();
    });
  }

  document.querySelectorAll("[data-medium-editor]").forEach(initializeEditor);
  document.addEventListener("formset:added", (event) => {
    if (event.target.matches?.("[data-medium-editor]")) initializeEditor(event.target);
    event.target.querySelectorAll?.("[data-medium-editor]").forEach(initializeEditor);
  });
});
