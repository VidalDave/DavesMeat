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
    const mode = orderForm.dataset.deliveryMode;
    const allowed = new Set((orderForm.dataset.allowedWeekdays || "").split(",").filter(Boolean).map(Number));
    const validateDate = () => {
      if (!dateInput.value || mode !== "weekdays") {
        dateInput.setCustomValidity("");
        return;
      }
      const weekday = new Date(dateInput.value + "T00:00:00").getDay();
      dateInput.setCustomValidity(allowed.has(weekday) ? "" : "תאריך זה אינו זמין לאספקה");
    };
    dateInput.addEventListener("change", validateDate);
    orderForm.addEventListener("submit", validateDate);
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
      form.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
})();

