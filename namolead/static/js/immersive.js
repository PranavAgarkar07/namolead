document.addEventListener("DOMContentLoaded", () => {
  // Sticky nav shadow
  const nav = document.querySelector(".govuk-header");
  if (nav) {
    const onScroll = () => {
      if (window.scrollY > 8) {
        nav.style.boxShadow = "0 4px 24px rgba(0, 0, 0, 0.15)";
      } else {
        nav.style.boxShadow = "none";
      }
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  // Mobile Hamburger Menu (if using mobile nav drawer)
  const menuBtn = document.getElementById("mobile-menu-btn");
  const menuDrawer = document.getElementById("mobile-menu-drawer");
  const iconOpen = document.getElementById("hamburger-icon-open");
  const iconClose = document.getElementById("hamburger-icon-close");

  if (menuBtn && menuDrawer) {
    const toggleMenu = () => {
      const isExpanded = menuBtn.getAttribute("aria-expanded") === "true";
      const nextState = !isExpanded;
      menuBtn.setAttribute("aria-expanded", String(nextState));
      menuDrawer.classList.toggle("hidden", isExpanded);
      if (iconOpen && iconClose) {
        iconOpen.classList.toggle("hidden", nextState);
        iconClose.classList.toggle("hidden", !nextState);
      }
    };

    menuBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleMenu();
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && menuBtn.getAttribute("aria-expanded") === "true") {
        toggleMenu();
      }
    });

    document.addEventListener("click", (e) => {
      if (
        menuBtn.getAttribute("aria-expanded") === "true" &&
        !menuDrawer.contains(e.target) &&
        !menuBtn.contains(e.target)
      ) {
        toggleMenu();
      }
    });
  }

  // Scroll reveal (simplified — no animations, just show)
  const revealEls = document.querySelectorAll(".reveal");
  if (!("IntersectionObserver" in window) || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    revealEls.forEach((el) => el.classList.add("is-visible"));
    return;
  }

  const io = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        if (e.isIntersecting) {
          e.target.classList.add("is-visible");
          io.unobserve(e.target);
        }
      }
    },
    { threshold: 0.1, rootMargin: "0px 0px -30px 0px" }
  );

  revealEls.forEach((el) => io.observe(el));
});
