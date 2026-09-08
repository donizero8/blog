document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-profile-image-widget]").forEach((widget) => {
    const input = widget.querySelector("[data-profile-image-input]");
    const dialog = widget.querySelector("[data-profile-crop-dialog]");
    const stage = widget.querySelector("[data-profile-crop-stage]");
    const canvas = widget.querySelector("[data-profile-crop-canvas]");
    const zoom = widget.querySelector("[data-profile-crop-zoom]");
    const status = widget.querySelector("[data-profile-crop-status]");
    const context = canvas.getContext("2d");
    let image = null;
    let filename = "profile.jpg";
    let baseScale = 1;
    let offsetX = 0;
    let offsetY = 0;
    let pointer = null;

    function scale() {
      return baseScale * (Number(zoom.value) / 100);
    }

    function clampOffsets() {
      const width = image.width * scale();
      const height = image.height * scale();
      const limitX = Math.max(0, (width - canvas.width) / 2);
      const limitY = Math.max(0, (height - canvas.height) / 2);
      offsetX = Math.max(-limitX, Math.min(limitX, offsetX));
      offsetY = Math.max(-limitY, Math.min(limitY, offsetY));
    }

    function draw() {
      if (!image) return;
      clampOffsets();
      const width = image.width * scale();
      const height = image.height * scale();
      context.clearRect(0, 0, canvas.width, canvas.height);
      context.drawImage(
        image,
        (canvas.width - width) / 2 + offsetX,
        (canvas.height - height) / 2 + offsetY,
        width,
        height,
      );
    }

    input.addEventListener("change", () => {
      const file = input.files[0];
      if (!file) return;
      if (!file.type.startsWith("image/")) {
        input.value = "";
        return;
      }
      filename = file.name;
      const url = URL.createObjectURL(file);
      const nextImage = new Image();
      nextImage.onload = () => {
        URL.revokeObjectURL(url);
        image = nextImage;
        baseScale = Math.max(canvas.width / image.width, canvas.height / image.height);
        offsetX = 0;
        offsetY = 0;
        zoom.value = "100";
        status.textContent = "";
        draw();
        dialog.showModal();
      };
      nextImage.onerror = () => {
        URL.revokeObjectURL(url);
        input.value = "";
        status.textContent = "Gambar tidak dapat dibuka.";
      };
      nextImage.src = url;
    });

    zoom.addEventListener("input", draw);
    stage.addEventListener("pointerdown", (event) => {
      if (!image) return;
      pointer = {id: event.pointerId, x: event.clientX, y: event.clientY};
      stage.setPointerCapture(event.pointerId);
      stage.classList.add("is-dragging");
    });
    stage.addEventListener("pointermove", (event) => {
      if (!pointer || pointer.id !== event.pointerId) return;
      const ratio = canvas.width / stage.getBoundingClientRect().width;
      offsetX += (event.clientX - pointer.x) * ratio;
      offsetY += (event.clientY - pointer.y) * ratio;
      pointer.x = event.clientX;
      pointer.y = event.clientY;
      draw();
    });
    function stopDragging(event) {
      if (!pointer || pointer.id !== event.pointerId) return;
      pointer = null;
      stage.classList.remove("is-dragging");
    }
    stage.addEventListener("pointerup", stopDragging);
    stage.addEventListener("pointercancel", stopDragging);

    function cancelCrop() {
      dialog.close();
      input.value = "";
      image = null;
    }
    widget.querySelectorAll("[data-profile-crop-cancel]").forEach((button) => {
      button.addEventListener("click", cancelCrop);
    });
    dialog.addEventListener("cancel", (event) => {
      event.preventDefault();
      cancelCrop();
    });
    widget.querySelector("[data-profile-crop-apply]").addEventListener("click", () => {
      if (!image) return;
      canvas.toBlob((blob) => {
        if (!blob) {
          status.textContent = "Foto gagal diproses.";
          return;
        }
        const data = new DataTransfer();
        const stem = filename.replace(/\.[^.]+$/, "") || "profile";
        data.items.add(new File([blob], `${stem}-cropped.jpg`, {type: "image/jpeg"}));
        input.files = data.files;
        dialog.close();
        image = null;
      }, "image/jpeg", 0.9);
    });
  });
});
