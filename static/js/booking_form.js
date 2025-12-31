// Additional JavaScript validation for phone number input
(function () {
  const phoneInput = document.getElementById("booking-phone");
  const bookingForm = document.getElementById("booking-form");
  const emailInput = document.getElementById("booking-email");
  // Check if user is registered by checking if email field is readonly
  const isRegistered = emailInput && emailInput.hasAttribute("readonly");

  if (phoneInput) {
    // Skip validation for registered users (all fields are disabled/readonly)
    if (isRegistered) {
      return;
    }

    // Real-time validation: remove non-numeric characters except +, -, (, ), and spaces
    if (phoneInput.tagName === "INPUT") {
      phoneInput.addEventListener("input", function (e) {
        let value = e.target.value.replace(/[^0-9+\-() ]/g, "");
        if (value !== e.target.value) {
          e.target.value = value;
        }

        // Update validity
        if (value.trim().length === 0) {
          phoneInput.setCustomValidity("Phone number is required.");
        } else if (!/[0-9]/.test(value)) {
          phoneInput.setCustomValidity(
            "Phone number must contain at least one digit."
          );
        } else {
          phoneInput.setCustomValidity("");
        }
      });

      // Prevent non-numeric characters on keypress
      phoneInput.addEventListener("keypress", function (e) {
        const allowedKeys = [
          "Backspace",
          "Delete",
          "Tab",
          "Escape",
          "Enter",
        ];
        const char = String.fromCharCode(e.which || e.keyCode);
        const isNumber = /[0-9]/.test(char);
        const isAllowedKey =
          allowedKeys.includes(e.key) ||
          ["+", "-", "(", ")", " "].includes(char);

        if (!isNumber && !isAllowedKey) {
          e.preventDefault();
        }
      });
    }

    // Form submission validation
    if (bookingForm && !isRegistered) {
      bookingForm.addEventListener("submit", function (e) {
        const phoneValue = phoneInput.value
          ? phoneInput.value.trim()
          : "";
        if (!phoneValue || phoneValue.length === 0) {
          e.preventDefault();
          phoneInput.setCustomValidity("Phone number is required.");
          phoneInput.reportValidity();
          phoneInput.focus();
          return false;
        }

        // Check if there's at least one digit
        if (!/[0-9]/.test(phoneValue)) {
          e.preventDefault();
          phoneInput.setCustomValidity(
            "Phone number must contain at least one digit."
          );
          phoneInput.reportValidity();
          phoneInput.focus();
          return false;
        }
      });
    }
  }
})();

