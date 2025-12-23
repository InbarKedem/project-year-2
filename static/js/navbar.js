/**
 * Mobile Navigation Toggle
 * Handles hamburger menu for mobile devices
 */

document.addEventListener("DOMContentLoaded", function () {
  const navToggle = document.getElementById("navToggle");
  const navList = document.getElementById("navList");

  if (!navToggle || !navList) return;

  navToggle.addEventListener("click", function () {
    navToggle.classList.toggle("nav__toggle--active");
    navList.classList.toggle("nav__list--open");

    // Prevent body scroll when menu is open
    if (navList.classList.contains("nav__list--open")) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
  });

  // Close menu when clicking on a link
  const navLinks = navList.querySelectorAll(".nav__link");
  navLinks.forEach((link) => {
    link.addEventListener("click", function () {
      navToggle.classList.remove("nav__toggle--active");
      navList.classList.remove("nav__list--open");
      document.body.style.overflow = "";
    });
  });

  // Close menu when clicking outside
  document.addEventListener("click", function (event) {
    const isClickInsideNav =
      navList.contains(event.target) || navToggle.contains(event.target);

    if (!isClickInsideNav && navList.classList.contains("nav__list--open")) {
      navToggle.classList.remove("nav__toggle--active");
      navList.classList.remove("nav__list--open");
      document.body.style.overflow = "";
    }
  });

  // Close menu on window resize if it goes above 768px
  window.addEventListener("resize", function () {
    if (window.innerWidth > 768) {
      navToggle.classList.remove("nav__toggle--active");
      navList.classList.remove("nav__list--open");
      document.body.style.overflow = "";
    }
  });
});
