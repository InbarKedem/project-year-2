// Register Form Validation
(function () {
  const registerForm = document.querySelector(".register-form");
  
  if (!registerForm) {
    return;
  }

  // Get form fields
  const firstNameInput = document.getElementById("reg-first-name");
  const middleNameInput = document.getElementById("reg-middle-name");
  const lastNameInput = document.getElementById("reg-last-name");
  const emailInput = document.getElementById("reg-email");
  const phoneInput = document.getElementById("reg-phone");

  // Validation functions
  function validateName(name, isRequired = true) {
    if (!name) {
      return isRequired ? "This field is required." : "";
    }
    
    const trimmed = name.trim();
    if (isRequired && trimmed.length === 0) {
      return "This field is required.";
    }
    
    if (trimmed.length > 0) {
      // Allow letters, spaces, hyphens, and apostrophes
      const namePattern = /^[a-zA-Z\s'-]+$/;
      if (!namePattern.test(trimmed)) {
        return "Name must contain only letters, spaces, hyphens, and apostrophes.";
      }
      
      // Check for consecutive special characters
      if (/['-]{2,}/.test(trimmed) || /^\s|\s$/.test(trimmed)) {
        return "Name format is invalid.";
      }
    }
    
    return "";
  }

  function validateEmail(email) {
    if (!email || email.trim().length === 0) {
      return "Email is required.";
    }
    
    const trimmed = email.trim();
    // Standard email regex pattern
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (!emailPattern.test(trimmed)) {
      return "Please enter a valid email address.";
    }
    
    // Additional check for valid domain
    const parts = trimmed.split("@");
    if (parts.length !== 2 || parts[0].length === 0 || parts[1].length === 0) {
      return "Please enter a valid email address.";
    }
    
    return "";
  }

  function validatePhone(phone) {
    if (!phone || phone.trim().length === 0) {
      return "Phone number is required.";
    }
    
    const trimmed = phone.trim();
    
    // Remove formatting characters for validation
    const digitsOnly = trimmed.replace(/[^0-9]/g, "");
    
    if (digitsOnly.length < 10) {
      return "Phone number must contain at least 10 digits.";
    }
    
    // Check if phone contains valid characters (digits, +, -, parentheses, spaces)
    const phonePattern = /^[\d\s+\-()]+$/;
    if (!phonePattern.test(trimmed)) {
      return "Phone number contains invalid characters.";
    }
    
    return "";
  }

  // Helper function to show error message
  function showError(input, message) {
    const formGroup = input.parentElement;
    
    // Remove existing error message
    const existingError = formGroup.querySelector(".form-error");
    if (existingError) {
      existingError.remove();
    }
    
    // Remove error class from form group
    formGroup.classList.remove("form-group--error");
    
    if (message) {
      // Add error class to form group
      formGroup.classList.add("form-group--error");
      
      // Create and add error message element
      const errorElement = document.createElement("span");
      errorElement.className = "form-error";
      errorElement.setAttribute("role", "alert");
      errorElement.textContent = message;
      formGroup.appendChild(errorElement);
      
      // Set custom validity
      input.setCustomValidity(message);
    } else {
      input.setCustomValidity("");
    }
  }

  // Real-time validation on blur
  if (firstNameInput) {
    firstNameInput.addEventListener("blur", function () {
      const error = validateName(this.value, true);
      showError(this, error);
    });
    
    firstNameInput.addEventListener("input", function () {
      // Clear error on input if field becomes valid
      if (this.parentElement.classList.contains("form-group--error")) {
        const error = validateName(this.value, true);
        if (!error) {
          showError(this, "");
        }
      }
    });
  }

  if (middleNameInput) {
    middleNameInput.addEventListener("blur", function () {
      const error = validateName(this.value, false);
      showError(this, error);
    });
    
    middleNameInput.addEventListener("input", function () {
      if (this.parentElement.classList.contains("form-group--error")) {
        const error = validateName(this.value, false);
        if (!error) {
          showError(this, "");
        }
      }
    });
  }

  if (lastNameInput) {
    lastNameInput.addEventListener("blur", function () {
      const error = validateName(this.value, true);
      showError(this, error);
    });
    
    lastNameInput.addEventListener("input", function () {
      if (this.parentElement.classList.contains("form-group--error")) {
        const error = validateName(this.value, true);
        if (!error) {
          showError(this, "");
        }
      }
    });
  }

  if (emailInput) {
    emailInput.addEventListener("blur", function () {
      const error = validateEmail(this.value);
      showError(this, error);
    });
    
    emailInput.addEventListener("input", function () {
      if (this.parentElement.classList.contains("form-group--error")) {
        const error = validateEmail(this.value);
        if (!error) {
          showError(this, "");
        }
      }
    });
  }

  if (phoneInput) {
    // Real-time formatting: allow only valid phone characters
    phoneInput.addEventListener("input", function (e) {
      let value = e.target.value.replace(/[^0-9+\-() ]/g, "");
      if (value !== e.target.value) {
        e.target.value = value;
      }
      
      // Clear error if field becomes valid
      if (this.parentElement.classList.contains("form-group--error")) {
        const error = validatePhone(this.value);
        if (!error) {
          showError(this, "");
        }
      }
    });
    
    phoneInput.addEventListener("blur", function () {
      const error = validatePhone(this.value);
      showError(this, error);
    });
    
    // Prevent invalid characters on keypress
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
  registerForm.addEventListener("submit", function (e) {
    let isValid = true;
    let firstInvalidField = null;
    const errors = [];

    // Validate first name
    if (firstNameInput) {
      const error = validateName(firstNameInput.value, true);
      if (error) {
        showError(firstNameInput, error);
        isValid = false;
        errors.push("First Name: " + error);
        if (!firstInvalidField) {
          firstInvalidField = firstNameInput;
        }
      } else {
        showError(firstNameInput, "");
      }
    }

    // Validate middle name (optional)
    if (middleNameInput && middleNameInput.value.trim().length > 0) {
      const error = validateName(middleNameInput.value, false);
      if (error) {
        showError(middleNameInput, error);
        isValid = false;
        errors.push("Middle Name: " + error);
        if (!firstInvalidField) {
          firstInvalidField = middleNameInput;
        }
      } else {
        showError(middleNameInput, "");
      }
    }

    // Validate last name
    if (lastNameInput) {
      const error = validateName(lastNameInput.value, true);
      if (error) {
        showError(lastNameInput, error);
        isValid = false;
        errors.push("Last Name: " + error);
        if (!firstInvalidField) {
          firstInvalidField = lastNameInput;
        }
      } else {
        showError(lastNameInput, "");
      }
    }

    // Validate email
    if (emailInput) {
      const error = validateEmail(emailInput.value);
      if (error) {
        showError(emailInput, error);
        isValid = false;
        errors.push("Email: " + error);
        if (!firstInvalidField) {
          firstInvalidField = emailInput;
        }
      } else {
        showError(emailInput, "");
      }
    }

    // Validate phone
    if (phoneInput) {
      const error = validatePhone(phoneInput.value);
      if (error) {
        showError(phoneInput, error);
        isValid = false;
        errors.push("Phone: " + error);
        if (!firstInvalidField) {
          firstInvalidField = phoneInput;
        }
      } else {
        showError(phoneInput, "");
      }
    }

    if (!isValid) {
      e.preventDefault();
      
      // Show popup error message with summary
      if (window.popupManager && errors.length > 0) {
        const errorMessage = errors.length === 1 
          ? errors[0] 
          : "Please fix the following errors: " + errors.map((err, idx) => `${idx + 1}. ${err}`).join(" | ");
        window.popupManager.error(errorMessage, 8000);
      }
      
      if (firstInvalidField) {
        firstInvalidField.focus();
        firstInvalidField.reportValidity();
      }
      return false;
    }
  });
})();

