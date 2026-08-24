(() => {
  const input = document.getElementById("search-input");
  const grid = document.getElementById("opportunity-grid");
  const form = document.getElementById("search-form");
  const meta = document.getElementById("search-meta");
  const countEl = document.getElementById("search-count");
  const queryEl = document.getElementById("search-query");
  const clearBtn = document.getElementById("search-clear");
  const spinner = document.getElementById("search-spinner");
  let categoryInput = document.getElementById("search-category");
  const filterBtns = document.querySelectorAll("[data-filter-btn]");
  const directorySection = document.getElementById("directory") || document.getElementById("opportunities");

  if (!grid) return;

  if (!categoryInput && form) {
    categoryInput = document.createElement("input");
    categoryInput.type = "hidden";
    categoryInput.name = "category";
    categoryInput.id = "search-category";
    form.appendChild(categoryInput);
  }

  function scrollToDirectory() {
    if (directorySection) {
      const topOffset = 100;
      const elementPosition = directorySection.getBoundingClientRect().top;
      const offsetPosition = elementPosition + window.pageYOffset - topOffset;
      window.scrollTo({
        top: offsetPosition,
        behavior: "smooth"
      });
    }
  }

  function updateUrl(q, category) {
    const url = new URL(window.location.href);
    if (q) url.searchParams.set("q", q);
    else url.searchParams.delete("q");

    if (category) url.searchParams.set("category", category);
    else url.searchParams.delete("category");

    window.history.replaceState(null, "", url.pathname + url.search);
  }

  let timer = null;
  let controller = null;

  async function runSearch(q, category, shouldScroll = false) {
    if (controller) controller.abort();
    controller = new AbortController();
    grid.style.opacity = "0.6";
    if (spinner) spinner.style.display = "inline-block";

    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (category) params.set("category", category);
    if (!q && !category) params.set("all", "1");

    try {
      const res = await fetch(`/api/search/?${params.toString()}`, {
        signal: controller.signal,
        headers: { Accept: "application/json" },
      });
      if (!res.ok) throw new Error("search request failed");
      const data = await res.json();

      if (data.count === 0) {
        grid.innerHTML = `
          <div class="govuk-grid-column-full">
            <div class="govuk-inset-text" style="text-align: center; padding: 30px;">
              <i class="fa-solid fa-magnifying-glass" style="font-size: 24px; color: var(--govuk-secondary-text); margin-bottom: 10px; display: block;"></i>
              <h3 class="govuk-heading-m">No opportunities found</h3>
              <p class="govuk-body">Nothing matches your search or filter selection. Try selecting "All" or a broader search term.</p>
            </div>
          </div>
        `;
      } else {
        grid.innerHTML = data.html;
      }
      grid.style.opacity = "1";
      if (spinner) spinner.style.display = "none";

      if (countEl) countEl.textContent = data.count;
      if (queryEl) queryEl.textContent = q || category;

      if (meta) {
        if (q) {
          meta.style.display = "block";
        } else {
          meta.style.display = "none";
        }
      }

      updateUrl(q, category);

      if (shouldScroll) {
        scrollToDirectory();
      }
    } catch (err) {
      if (err.name !== "AbortError") {
        grid.style.opacity = "1";
        if (spinner) spinner.style.display = "none";
      }
    }
  }

  function clearSearch() {
    if (controller) controller.abort();
    clearTimeout(timer);
    if (input) input.value = "";
    const activeCategory = categoryInput ? categoryInput.value : "";
    runSearch("", activeCategory, false);
    if (input) input.focus();
  }

  filterBtns.forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const targetCategory = btn.getAttribute("data-category") || "";

      filterBtns.forEach((b) => {
        const isSelected = b === btn;
        b.classList.remove("nlc-filter-tag--active");
        b.removeAttribute("aria-current");
        if (isSelected) {
          b.classList.add("nlc-filter-tag--active");
          b.setAttribute("aria-current", "page");
        }
      });

      if (categoryInput) {
        categoryInput.value = targetCategory;
      }

      const q = input ? input.value.trim() : "";
      runSearch(q, targetCategory, true);
    });
  });

  if (input) {
    input.addEventListener("input", () => {
      clearTimeout(timer);
      const q = input.value.trim();
      const cat = categoryInput ? categoryInput.value : "";
      timer = setTimeout(() => runSearch(q, cat, false), 250);
    });

    input.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && input.value) clearSearch();
    });
  }

  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const q = input ? input.value.trim() : "";
      const cat = categoryInput ? categoryInput.value : "";
      runSearch(q, cat, true);
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener("click", (e) => {
      e.preventDefault();
      clearSearch();
    });
  }
})();
