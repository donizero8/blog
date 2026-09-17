(() => {
  "use strict";

  const initialize = () => {
    const status = document.getElementById("id_status");
    const progressSection = document.querySelector("fieldset.book-progress-section");
    const startedAt = document.getElementById("id_started_at");
    const finishedAt = document.getElementById("id_finished_at");

    if (!status || !progressSection) return;

    const updateProgressVisibility = () => {
      const isWantToRead = status.value === "want";
      progressSection.hidden = isWantToRead;
      progressSection.setAttribute("aria-hidden", String(isWantToRead));
    };

    status.addEventListener("change", updateProgressVisibility);
    updateProgressVisibility();

    if (startedAt && finishedAt) {
      const row = startedAt.closest(".form-row");
      row?.classList.add("book-date-range");
      const parseDate = value => value ? new Date(`${value}T00:00:00`) : null;
      const isoDate = date => {
        const offset = date.getTimezoneOffset() * 60000;
        return new Date(date - offset).toISOString().slice(0, 10);
      };
      const formatDate = value => value ? new Intl.DateTimeFormat("id-ID", {
        day: "numeric", month: "short", year: "numeric"
      }).format(parseDate(value)) : "Pilih tanggal";

      const picker = document.createElement("div");
      picker.className = "book-range-picker";
      picker.innerHTML = `
        <button type="button" class="book-range-trigger" id="book-range-trigger" aria-haspopup="dialog" aria-expanded="false">
          <strong data-range-label></strong>
          <span class="book-range-icon" aria-hidden="true">▣</span>
        </button>
        <div class="book-range-popover" role="dialog" aria-label="Pilih rentang tanggal membaca" hidden>
          <header>
            <button type="button" data-month-previous aria-label="Bulan sebelumnya">‹</button>
            <strong data-month-label></strong>
            <button type="button" data-month-next aria-label="Bulan berikutnya">›</button>
          </header>
          <div class="book-range-weekdays" aria-hidden="true"><span>Sen</span><span>Sel</span><span>Rab</span><span>Kam</span><span>Jum</span><span>Sab</span><span>Min</span></div>
          <div class="book-range-days" role="grid"></div>
          <footer><button type="button" data-range-clear>Hapus rentang</button><button type="button" data-range-today>Hari ini</button><span data-date-duration aria-live="polite"></span></footer>
        </div>`;
      const rangeLabel = document.createElement("label");
      rangeLabel.className = "book-range-field-label";
      rangeLabel.htmlFor = "book-range-trigger";
      rangeLabel.textContent = "Rentang membaca:";
      row?.append(rangeLabel, picker);

      const trigger = picker.querySelector(".book-range-trigger");
      const popover = picker.querySelector(".book-range-popover");
      const daysGrid = picker.querySelector(".book-range-days");
      const label = picker.querySelector("[data-range-label]");
      const monthLabel = picker.querySelector("[data-month-label]");
      const duration = picker.querySelector("[data-date-duration]");
      let choosingEnd = Boolean(startedAt.value && !finishedAt.value);
      const initial = parseDate(startedAt.value) || new Date();
      let visibleMonth = new Date(initial.getFullYear(), initial.getMonth(), 1);

      const updateSummary = () => {
        finishedAt.min = startedAt.value || "";
        label.textContent = startedAt.value
          ? `${formatDate(startedAt.value)} — ${finishedAt.value ? formatDate(finishedAt.value) : "Pilih tanggal selesai"}`
          : "Pilih tanggal mulai dan selesai";
        if (!startedAt.value || !finishedAt.value) {
          duration.textContent = "";
        } else {
          const days = Math.round((parseDate(finishedAt.value) - parseDate(startedAt.value)) / 86400000);
          duration.textContent = `${days + 1} hari`;
        }
      };

      const renderCalendar = () => {
        monthLabel.textContent = new Intl.DateTimeFormat("id-ID", {month: "long", year: "numeric"}).format(visibleMonth);
        daysGrid.replaceChildren();
        const firstOffset = (visibleMonth.getDay() + 6) % 7;
        const count = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() + 1, 0).getDate();
        for (let index = 0; index < firstOffset; index += 1) {
          const spacer = document.createElement("span");
          spacer.className = "book-range-spacer";
          daysGrid.append(spacer);
        }
        const start = parseDate(startedAt.value);
        const end = parseDate(finishedAt.value);
        const today = isoDate(new Date());
        for (let day = 1; day <= count; day += 1) {
          const date = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth(), day);
          const value = isoDate(date);
          const button = document.createElement("button");
          button.type = "button";
          button.textContent = day;
          button.dataset.date = value;
          button.setAttribute("role", "gridcell");
          button.setAttribute("aria-label", formatDate(value));
          if (value === today) button.classList.add("is-today");
          if (start && end && date >= start && date <= end) button.classList.add("is-in-range");
          if (value === startedAt.value) button.classList.add("is-range-start");
          if (value === finishedAt.value) button.classList.add("is-range-end");
          daysGrid.append(button);
        }
      };

      const closePicker = () => {
        popover.hidden = true;
        trigger.setAttribute("aria-expanded", "false");
      };
      trigger.addEventListener("click", () => {
        popover.hidden = !popover.hidden;
        trigger.setAttribute("aria-expanded", String(!popover.hidden));
        if (!popover.hidden) {
          renderCalendar();
          const triggerRect = trigger.getBoundingClientRect();
          popover.classList.toggle("is-above", window.innerHeight - triggerRect.bottom < 430 && triggerRect.top > 410);
        }
      });
      daysGrid.addEventListener("click", event => {
        const value = event.target.closest("[data-date]")?.dataset.date;
        if (!value) return;
        if (!choosingEnd || !startedAt.value) {
          startedAt.value = value;
          finishedAt.value = "";
          choosingEnd = true;
        } else {
          if (value < startedAt.value) {
            finishedAt.value = startedAt.value;
            startedAt.value = value;
          } else {
            finishedAt.value = value;
          }
          choosingEnd = false;
          closePicker();
        }
        updateSummary();
        renderCalendar();
      });
      picker.querySelector("[data-month-previous]").addEventListener("click", () => {
        visibleMonth = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() - 1, 1);
        renderCalendar();
      });
      picker.querySelector("[data-month-next]").addEventListener("click", () => {
        visibleMonth = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() + 1, 1);
        renderCalendar();
      });
      picker.querySelector("[data-range-clear]").addEventListener("click", () => {
        startedAt.value = "";
        finishedAt.value = "";
        choosingEnd = false;
        updateSummary();
        renderCalendar();
      });
      picker.querySelector("[data-range-today]").addEventListener("click", () => {
        const today = isoDate(new Date());
        startedAt.value = today;
        finishedAt.value = today;
        visibleMonth = new Date();
        choosingEnd = false;
        updateSummary();
        renderCalendar();
        closePicker();
      });
      document.addEventListener("click", event => {
        if (!picker.contains(event.target)) closePicker();
      });
      picker.addEventListener("keydown", event => {
        if (event.key === "Escape") closePicker();
      });
      updateSummary();
    }
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize, { once: true });
  } else {
    initialize();
  }
})();
