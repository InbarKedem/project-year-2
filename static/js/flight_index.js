// Automatically show all flights by default when page loads with no search parameters
(function () {
  const urlParams = new URLSearchParams(window.location.search);
  const hasSearchParams =
    urlParams.has("source") ||
    urlParams.has("dest") ||
    urlParams.has("date") ||
    urlParams.has("min_price") ||
    urlParams.has("max_price") ||
    urlParams.has("class") ||
    urlParams.has("show_all");

  // Check if flights results container exists (flights were loaded)
  const flightsContainer = document.querySelector(".results-container");
  const flightsNotLoaded = flightsContainer === null;

  // Get the show all URL from data attribute or use default
  const showAllLink = document.querySelector("[data-show-all-url]");
  const showAllUrl = showAllLink
    ? showAllLink.getAttribute("data-show-all-url")
    : null;

  // If no search parameters and flights are not displayed, automatically show all flights
  if (!hasSearchParams && flightsNotLoaded && showAllUrl) {
    window.location.href = showAllUrl;
  }
})();
