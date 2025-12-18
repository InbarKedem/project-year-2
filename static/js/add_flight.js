document.addEventListener("DOMContentLoaded", function () {
  const sourceSelect = document.getElementById("source_id");
  const destSelect = document.getElementById("dest_id");
  const timeInput = document.getElementById("departure_time");
  const aircraftSelect = document.getElementById("aircraft_id");
  const pilotsContainer = document.getElementById("pilots_container");
  const attendantsContainer = document.getElementById("attendants_container");

  function checkAvailability() {
    const sourceId = sourceSelect.value;
    const destId = destSelect.value;
    const departureTime = timeInput.value;
    const aircraftId = aircraftSelect.value;

    if (sourceId && destId && sourceId === destId) {
      alert("Source and Destination airports cannot be the same.");
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
      input.addEventListener("change", function () {
        validateSelection(container, requiredCount, type);
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
  }

  function validateSelection(container, maxCount, type) {
    const checkboxes = container.querySelectorAll(`input[data-type="${type}"]`);
    let checkedCount = 0;
    checkboxes.forEach((cb) => {
      if (cb.checked) checkedCount++;
    });

    if (checkedCount > maxCount) {
      alert(`You can only select ${maxCount} ${type}.`);
      // Uncheck the last one
      event.target.checked = false;
    }
  }

  if (sourceSelect && destSelect && timeInput && aircraftSelect) {
    sourceSelect.addEventListener("change", checkAvailability);
    destSelect.addEventListener("change", checkAvailability);
    timeInput.addEventListener("change", checkAvailability);
    aircraftSelect.addEventListener("change", checkAvailability);

    // Check on load if values are pre-filled (e.g. browser cache or edit mode)
    checkAvailability();
  }
});
