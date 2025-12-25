document.addEventListener("DOMContentLoaded", function () {
  const sourceSelect = document.getElementById("source_id");
  const destSelect = document.getElementById("dest_id");
  const timeInput = document.getElementById("departure_time");
  const aircraftSelect = document.getElementById("aircraft_id");
  const pilotsContainer = document.getElementById("pilots_container");
  const attendantsContainer = document.getElementById("attendants_container");

  // Store current requirements for form validation
  let currentRequirements = { pilots: 2, attendants: 3 };

  // Set default departure time to current time if not already set
  if (timeInput && !timeInput.value) {
    const now = new Date();
    // Format as YYYY-MM-DDTHH:mm for datetime-local input
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, "0");
    const day = String(now.getDate()).padStart(2, "0");
    const hours = String(now.getHours()).padStart(2, "0");
    const minutes = String(now.getMinutes()).padStart(2, "0");
    timeInput.value = `${year}-${month}-${day}T${hours}:${minutes}`;
  }

  // Update min attribute dynamically to always be current time
  function updateMinDateTime() {
    if (timeInput) {
      const now = new Date();
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, "0");
      const day = String(now.getDate()).padStart(2, "0");
      const hours = String(now.getHours()).padStart(2, "0");
      const minutes = String(now.getMinutes()).padStart(2, "0");
      timeInput.min = `${year}-${month}-${day}T${hours}:${minutes}`;
    }
  }

  // Initialize min attribute
  updateMinDateTime();

  // Real-time validation for past dates
  let isUpdatingTime = false; // Flag to prevent infinite recursion
  function validateDepartureTime() {
    if (!timeInput || !timeInput.value || isUpdatingTime) return;

    const selectedDateTime = new Date(timeInput.value);
    const now = new Date();

    if (selectedDateTime < now) {
      window.popupManager.error("Departure time cannot be in the past.");
      // Reset to current time
      isUpdatingTime = true; // Set flag to prevent recursion
      updateMinDateTime();
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, "0");
      const day = String(now.getDate()).padStart(2, "0");
      const hours = String(now.getHours()).padStart(2, "0");
      const minutes = String(now.getMinutes()).padStart(2, "0");
      timeInput.value = `${year}-${month}-${day}T${hours}:${minutes}`;
      // Trigger change to update availability (but validation won't run due to flag)
      timeInput.dispatchEvent(new Event("change"));
      // Reset flag after a short delay
      setTimeout(() => {
        isUpdatingTime = false;
      }, 100);
    }
  }

  // Real-time validation for negative numbers in price fields
  function validatePriceInput(input, fieldName) {
    if (!input) return;

    const value = parseFloat(input.value);
    if (input.value !== "" && (isNaN(value) || value < 0)) {
      window.popupManager.error(`${fieldName} cannot be negative.`);
      input.value = "";
    }
  }

  function checkAvailability() {
    const sourceId = sourceSelect.value;
    const destId = destSelect.value;
    const departureTime = timeInput.value;
    const aircraftId = aircraftSelect.value;

    if (sourceId && destId && sourceId === destId) {
      window.popupManager.error(
        "Source and Destination airports cannot be the same."
      );
      // Reset destination or handle UI
      destSelect.value = "";
      return;
    }

    if (sourceId && destId && departureTime) {
      // Visual feedback
      pilotsContainer.style.opacity = "0.5";
      attendantsContainer.style.opacity = "0.5";

      fetch(
        `/api/check_availability?source_id=${sourceId}&dest_id=${destId}&departure_time=${departureTime}&aircraft_id=${aircraftId}`
      )
        .then((response) => response.json())
        .then((data) => {
          updateCrewLists(data);
          pilotsContainer.style.opacity = "1";
          attendantsContainer.style.opacity = "1";
        })
        .catch((error) => {
          console.error("Error:", error);
          pilotsContainer.style.opacity = "1";
          attendantsContainer.style.opacity = "1";
        });
    }
  }

  function updateCrewLists(data) {
    // Update Aircraft List
    updateAircraftList(data.aircrafts);

    // Clear current lists
    pilotsContainer.innerHTML = "";
    attendantsContainer.innerHTML = "";

    const crewData = data.crew;
    const requirements = data.requirements;

    // Store requirements for form validation
    currentRequirements = requirements;

    const pilots = crewData.filter((c) => c.role === "Pilot");
    const attendants = crewData.filter((c) => c.role === "Attendant");

    renderCrewList(pilots, pilotsContainer, requirements.pilots, "pilots");
    renderCrewList(
      attendants,
      attendantsContainer,
      requirements.attendants,
      "attendants"
    );
  }

  function updateAircraftList(aircrafts) {
    if (!aircrafts) return;

    const currentSelection = aircraftSelect.value;
    aircraftSelect.innerHTML = ""; // Clear existing options

    // Sort: Available first
    aircrafts.sort((a, b) =>
      a.is_available === b.is_available ? 0 : a.is_available ? -1 : 1
    );

    aircrafts.forEach((ac) => {
      const option = document.createElement("option");
      option.value = ac.aircraft_id;

      let text = `${ac.manufacturer} (ID: ${ac.aircraft_id})`;
      if (ac.is_large) text += " [Large]";

      if (!ac.is_available) {
        text += ` - UNAVAILABLE: ${ac.reason}`;
        option.disabled = true;
      }

      option.textContent = text;
      aircraftSelect.appendChild(option);
    });

    // Restore selection if possible and valid
    if (currentSelection) {
      const optionToSelect = aircraftSelect.querySelector(
        `option[value="${currentSelection}"]`
      );
      if (optionToSelect && !optionToSelect.disabled) {
        aircraftSelect.value = currentSelection;
      } else {
        // If previously selected is now invalid, select the first available
        const firstAvailable = aircraftSelect.querySelector(
          "option:not([disabled])"
        );
        if (firstAvailable) {
          aircraftSelect.value = firstAvailable.value;
          // Trigger change to update crew requirements
          aircraftSelect.dispatchEvent(new Event("change"));
        } else {
          aircraftSelect.value = "";
        }
      }
    } else {
      // Select first available
      const firstAvailable = aircraftSelect.querySelector(
        "option:not([disabled])"
      );
      if (firstAvailable) {
        aircraftSelect.value = firstAvailable.value;
        // Trigger change to update crew requirements
        aircraftSelect.dispatchEvent(new Event("change"));
      }
    }
  }

  function renderCrewList(crewList, container, requiredCount, type) {
    // Sort: Available first
    crewList.sort((a, b) =>
      a.is_available === b.is_available ? 0 : a.is_available ? -1 : 1
    );

    const availableCount = crewList.filter((c) => c.is_available).length;
    let selectedCount = 0;

    // Header for requirements
    const header = document.createElement("div");
    header.style.display = "flex";
    header.style.justifyContent = "space-between";
    header.style.marginBottom = "5px";

    const reqText = document.createElement("span");
    reqText.className = "text-muted small";
    reqText.textContent = `Required: ${requiredCount}`;
    header.appendChild(reqText);

    // Add selected count display
    const countDisplay = document.createElement("span");
    countDisplay.className = "selected-count";
    countDisplay.style.marginLeft = "10px";
    countDisplay.style.fontWeight = "bold";
    countDisplay.textContent = `Selected: 0/${requiredCount}`;
    countDisplay.style.color = "orange";
    header.appendChild(countDisplay);

    if (availableCount < requiredCount) {
      const warning = document.createElement("span");
      warning.style.color = "red";
      warning.style.fontWeight = "bold";
      warning.style.fontSize = "0.9em";
      warning.textContent = `⚠️ Only ${availableCount} available!`;
      header.appendChild(warning);
    }

    container.appendChild(header);

    if (crewList.length === 0) {
      const p = document.createElement("p");
      p.className = "text-muted";
      p.textContent = "No crew found.";
      container.appendChild(p);
      return;
    }

    crewList.forEach((person) => {
      const label = document.createElement("label");
      label.className = "checkbox-label";
      label.style.display = "flex";
      label.style.justifyContent = "space-between";
      label.style.alignItems = "center";

      const input = document.createElement("input");
      input.type = "checkbox";
      input.name = "crew_ids";
      input.value = person.id_number;
      input.dataset.type = type; // Store type for validation

      // Auto-select logic
      if (person.is_available && selectedCount < requiredCount) {
        input.checked = true;
        selectedCount++;
      }

      // Style for unavailable
      if (!person.is_available) {
        label.style.color = "#999";
        label.title = person.reason;
        input.disabled = true;
        input.checked = false;
      }

      // Add change listener for enforcement
      input.addEventListener("change", function (event) {
        validateSelection(container, requiredCount, type, event.target);
      });

      const textSpan = document.createElement("span");
      textSpan.textContent = `${person.first_name} ${person.last_name}`;

      if (!person.is_available) {
        const reasonSpan = document.createElement("span");
        reasonSpan.style.fontSize = "0.8em";
        reasonSpan.style.color = "red";
        reasonSpan.style.marginLeft = "10px";
        reasonSpan.textContent = `(${person.reason})`;
        textSpan.appendChild(reasonSpan);
      }

      label.prepend(input);
      label.appendChild(textSpan);
      container.appendChild(label);
    });

    // Update selected count display after rendering
    const checkedBoxes = container.querySelectorAll(
      `input[data-type="${type}"]:checked`
    );
    updateSelectedCount(container, checkedBoxes.length, requiredCount, type);
  }

  function validateSelection(container, maxCount, type, changedCheckbox) {
    const checkboxes = container.querySelectorAll(`input[data-type="${type}"]`);
    let checkedCount = 0;
    checkboxes.forEach((cb) => {
      if (cb.checked) checkedCount++;
    });

    if (checkedCount > maxCount) {
      window.popupManager.warning(`You can only select ${maxCount} ${type}.`);
      // Uncheck the checkbox that was just checked
      if (changedCheckbox) {
        changedCheckbox.checked = false;
      }
      return false;
    }

    // Update the selected count display
    updateSelectedCount(container, checkedCount, maxCount, type);
    return true;
  }

  function updateSelectedCount(container, selected, required, type) {
    // Find or create the count display
    let countDisplay = container.querySelector(".selected-count");
    if (!countDisplay) {
      countDisplay = document.createElement("span");
      countDisplay.className = "selected-count";
      countDisplay.style.marginLeft = "10px";
      countDisplay.style.fontWeight = "bold";
      const header = container.querySelector(".text-muted");
      if (header) {
        header.appendChild(countDisplay);
      }
    }

    countDisplay.textContent = `Selected: ${selected}/${required}`;
    if (selected > required) {
      countDisplay.style.color = "red";
    } else if (selected === required) {
      countDisplay.style.color = "green";
    } else {
      countDisplay.style.color = "orange";
    }
  }

  if (sourceSelect && destSelect && timeInput && aircraftSelect) {
    sourceSelect.addEventListener("change", checkAvailability);
    destSelect.addEventListener("change", checkAvailability);
    timeInput.addEventListener("change", checkAvailability);
    aircraftSelect.addEventListener("change", checkAvailability);

    // Real-time validation for departure time (past dates)
    timeInput.addEventListener("change", validateDepartureTime);
    timeInput.addEventListener("input", validateDepartureTime);

    // Check on load if values are pre-filled (e.g. browser cache or edit mode)
    checkAvailability();

    // Add real-time validation for price inputs
    const form = document.querySelector(".staff-form");
    if (form) {
      const economyPriceInput = form.querySelector(
        'input[name="economy_price"]'
      );
      const businessPriceInput = form.querySelector(
        'input[name="business_price"]'
      );

      if (economyPriceInput) {
        economyPriceInput.addEventListener("input", function () {
          validatePriceInput(economyPriceInput, "Economy price");
        });
        economyPriceInput.addEventListener("blur", function () {
          validatePriceInput(economyPriceInput, "Economy price");
        });
      }

      if (businessPriceInput) {
        businessPriceInput.addEventListener("input", function () {
          validatePriceInput(businessPriceInput, "Business price");
        });
        businessPriceInput.addEventListener("blur", function () {
          validatePriceInput(businessPriceInput, "Business price");
        });
      }

      // Add form validation before submission
      form.addEventListener("submit", function (event) {
        // Validate past dates/times
        if (timeInput && timeInput.value) {
          const selectedDateTime = new Date(timeInput.value);
          const now = new Date();
          if (selectedDateTime < now) {
            event.preventDefault();
            window.popupManager.error("Departure time cannot be in the past.");
            return false;
          }
        }

        // Validate prices are not negative
        const economyPriceInput = form.querySelector(
          'input[name="economy_price"]'
        );
        const businessPriceInput = form.querySelector(
          'input[name="business_price"]'
        );

        if (economyPriceInput && parseFloat(economyPriceInput.value) < 0) {
          event.preventDefault();
          window.popupManager.error("Economy price cannot be negative.");
          return false;
        }

        if (businessPriceInput && parseFloat(businessPriceInput.value) < 0) {
          event.preventDefault();
          window.popupManager.error("Business price cannot be negative.");
          return false;
        }

        const pilotCheckboxes = pilotsContainer.querySelectorAll(
          'input[data-type="pilots"]:checked'
        );
        const attendantCheckboxes = attendantsContainer.querySelectorAll(
          'input[data-type="attendants"]:checked'
        );

        // Use stored requirements
        const pilotRequired = currentRequirements.pilots || 2;
        const attendantRequired = currentRequirements.attendants || 3;

        if (pilotCheckboxes.length !== pilotRequired) {
          event.preventDefault();
          window.popupManager.error(
            `Please select exactly ${pilotRequired} pilot(s). Currently selected: ${pilotCheckboxes.length}`
          );
          return false;
        }

        if (attendantCheckboxes.length !== attendantRequired) {
          event.preventDefault();
          window.popupManager.error(
            `Please select exactly ${attendantRequired} attendant(s). Currently selected: ${attendantCheckboxes.length}`
          );
          return false;
        }

        return true;
      });
    }
  }
});
