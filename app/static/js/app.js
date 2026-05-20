(function () {
  const preview = document.querySelector("[data-image-preview]");
  document.querySelectorAll("[data-preview]").forEach((button) => {
    button.addEventListener("click", () => {
      const img = preview.querySelector("img");
      img.src = button.dataset.preview;
      preview.hidden = false;
    });
  });
  if (preview) {
    preview.addEventListener("click", () => {
      preview.hidden = true;
      preview.querySelector("img").src = "";
    });
  }

  const orderForm = document.querySelector(".order-form");
  if (orderForm) {
    const dateInput = orderForm.querySelector("[data-delivery-date]");
    const calendar = orderForm.querySelector("[data-pickup-calendar]");
    const mode = orderForm.dataset.deliveryMode;
    const allowed = new Set((orderForm.dataset.allowedWeekdays || "").split(",").filter(Boolean).map(Number));
    const hasSpecificPickupDays = mode === "weekdays" && allowed.size > 0;
    const today = new Date((calendar ? calendar.dataset.today : new Date().toISOString().slice(0, 10)) + "T00:00:00");
    let visibleMonth = new Date(today.getFullYear(), today.getMonth(), 1);

    const validateDate = () => {
      if (!dateInput.value) {
        dateInput.setCustomValidity("נא לבחור תאריך אספקה");
        return false;
      }
      const selectedDate = new Date(dateInput.value + "T00:00:00");
      if (selectedDate < today) {
        dateInput.setCustomValidity("תאריך זה אינו זמין לאספקה");
        return false;
      }
      if (!hasSpecificPickupDays) {
        dateInput.setCustomValidity("");
        return true;
      }
      const weekday = selectedDate.getDay();
      const valid = allowed.has(weekday);
      dateInput.setCustomValidity(valid ? "" : "תאריך זה אינו זמין לאספקה");
      return valid;
    };

    const formatDate = (date) => {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, "0");
      const day = String(date.getDate()).padStart(2, "0");
      return `${year}-${month}-${day}`;
    };

    const isAllowedDate = (date) => {
      if (date < today) return false;
      return !hasSpecificPickupDays || allowed.has(date.getDay());
    };

    const renderCalendar = () => {
      if (!calendar) return;
      const title = calendar.querySelector("[data-calendar-title]");
      const grid = calendar.querySelector("[data-calendar-grid]");
      title.textContent = visibleMonth.toLocaleDateString("he-IL", { month: "long", year: "numeric" });
      grid.innerHTML = "";

      const firstWeekday = visibleMonth.getDay();
      const daysInMonth = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() + 1, 0).getDate();
      for (let i = 0; i < firstWeekday; i += 1) {
        grid.appendChild(document.createElement("span"));
      }

      for (let day = 1; day <= daysInMonth; day += 1) {
        const current = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth(), day);
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = String(day);
        button.dataset.date = formatDate(current);
        button.disabled = !isAllowedDate(current);
        if (button.dataset.date === dateInput.value) {
          button.classList.add("selected");
        }
        button.addEventListener("click", () => {
          if (button.disabled) return;
          dateInput.value = button.dataset.date;
          validateDate();
          renderCalendar();
        });
        grid.appendChild(button);
      }
    };

    calendar?.querySelector("[data-calendar-prev]")?.addEventListener("click", () => {
      visibleMonth = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() - 1, 1);
      if (visibleMonth < new Date(today.getFullYear(), today.getMonth(), 1)) {
        visibleMonth = new Date(today.getFullYear(), today.getMonth(), 1);
      }
      renderCalendar();
    });
    calendar?.querySelector("[data-calendar-next]")?.addEventListener("click", () => {
      visibleMonth = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() + 1, 1);
      renderCalendar();
    });

    renderCalendar();
    orderForm.addEventListener("submit", (event) => {
      if (!validateDate()) {
        event.preventDefault();
        dateInput.reportValidity();
      }
    });
  }

  const productFile = document.querySelector("[data-product-file]");
  const uploadPreview = document.querySelector("[data-upload-preview]");
  if (productFile && uploadPreview) {
    productFile.addEventListener("change", () => {
      const file = productFile.files && productFile.files[0];
      if (!file) {
        uploadPreview.hidden = true;
        return;
      }
      uploadPreview.querySelector("img").src = URL.createObjectURL(file);
      uploadPreview.hidden = false;
    });
  }

  document.querySelectorAll("[data-edit-row]").forEach((button) => {
    button.addEventListener("click", () => {
      const row = JSON.parse(button.closest("[data-row]").dataset.row);
      const form = document.querySelector(".panel-form");
      Object.entries(row).forEach(([key, value]) => {
        const field = form.querySelector(`[name="${key}"], [name="${key.replace("id", "")}_id"]`);
        if (!field) return;
        if (field.type === "checkbox") {
          field.checked = Boolean(value);
        } else {
          field.value = value;
        }
      });
      const idField = form.querySelector("[data-edit-id]");
      if (idField) idField.value = row.id;
      const uploadPreview = form.querySelector("[data-upload-preview]");
      const fileField = form.querySelector("[data-product-file]");
      if (fileField) fileField.value = "";
      if (uploadPreview && (row.image_path || row.image_url)) {
        uploadPreview.querySelector("img").src = row.image_path || row.image_url;
        uploadPreview.hidden = false;
      }
      form.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
})();
