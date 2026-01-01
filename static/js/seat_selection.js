// Seat selection functionality for flight booking
// This file expects the following variables to be defined in the HTML:
// - economyPrice, businessPrice, hasEconomy, hasBusiness

let selectedSeats = [];
let classToggleTimeout = null;

function showClass(cls) {
  // Debounce rapid clicks to prevent UI lag
  if (classToggleTimeout) {
    clearTimeout(classToggleTimeout);
  }
  
  classToggleTimeout = setTimeout(() => {
    // Toggle Buttons
    document
      .getElementById("btn-economy")
      .classList.toggle("active", cls === "economy");
    document
      .getElementById("btn-business")
      .classList.toggle("active", cls === "business");

    // Toggle Maps
    const mapEconomy = document.getElementById("map-economy");
    const mapBusiness = document.getElementById("map-business");

    if (cls === "economy") {
      mapEconomy.classList.remove("hidden");
      mapBusiness.classList.add("hidden");
    } else {
      mapEconomy.classList.add("hidden");
      mapBusiness.classList.remove("hidden");
    }

    // Update Price Display (Initial)
    updatePriceDisplay(cls);
  }, 100); // 100ms debounce
}

function updatePriceDisplay(cls) {
  let priceDisplay = "";
  if (selectedSeats.length > 0) {
    let total = 0;
    selectedSeats.forEach((s) => {
      total += s.class === "business" ? businessPrice : economyPrice;
    });
    priceDisplay = `Total Price: $${total} (${selectedSeats.length} seats)`;
  } else {
    if (cls === "economy") {
      if (hasEconomy) priceDisplay = `Price: $${economyPrice}`;
      else priceDisplay = `Economy Sold Out ($${economyPrice})`;
    } else if (cls === "business") {
      if (hasBusiness) priceDisplay = `Price: $${businessPrice}`;
      else priceDisplay = `Business Sold Out ($${businessPrice})`;
    }
  }
  document.getElementById("selected-price-display").innerText = priceDisplay;
}

function clearSelection() {
  selectedSeats = [];
  document
    .querySelectorAll(".seat.selected")
    .forEach((el) => el.classList.remove("selected"));
  updateForm();
}

function selectSeat(element, isBusiness) {
  if (element.classList.contains("occupied")) return;

  const row = element.dataset.row;
  const col = element.dataset.col;
  const cls = isBusiness ? "business" : "economy";

  // Toggle selection
  const index = selectedSeats.findIndex(
    (s) => s.row === row && s.col === col && s.class === cls
  );
  if (index > -1) {
    // Deselect
    selectedSeats.splice(index, 1);
    element.classList.remove("selected");
  } else {
    // Select
    selectedSeats.push({ row, col, class: cls });
    element.classList.add("selected");
  }

  updateForm();
  updatePriceDisplay(cls);
}

function updateForm() {
  const container = document.getElementById("selected-seats-container");
  container.innerHTML = "";

  const extraContainer = document.getElementById(
    "extra-passengers-container"
  );
  extraContainer.innerHTML = "";

  if (selectedSeats.length === 0) {
    document.getElementById("confirm-btn").disabled = true;
    return;
  }

  document.getElementById("confirm-btn").disabled = false;

  // Add hidden inputs
  selectedSeats.forEach((s) => {
    const inputRow = document.createElement("input");
    inputRow.type = "hidden";
    inputRow.name = "seat_row";
    inputRow.value = s.row;
    container.appendChild(inputRow);

    const inputCol = document.createElement("input");
    inputCol.type = "hidden";
    inputCol.name = "seat_col";
    inputCol.value = s.col;
    container.appendChild(inputCol);

    const inputClass = document.createElement("input");
    inputClass.type = "hidden";
    inputClass.name = "seat_class";
    inputClass.value = s.class;
    container.appendChild(inputClass);
  });
}

