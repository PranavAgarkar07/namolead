(() => {
  const input = document.getElementById("search-input");
  const grid = document.getElementById("opportunity-grid");
  const form = document.getElementById("search-form");
  const meta = document.getElementById("search-meta");
  const countEl = document.getElementById("search-count");
  const queryEl = document.getElementById("search-query");
  const clearBtn = document.getElementById("search-clear");
  const spinner = document.getElementById("search-spinner");
  const categoryInput = document.getElementById("search-category");

  if (!input || !grid) return;

  const originalHtml = grid.innerHTML;

  function restoreGrid() {
    grid.innerHTML = originalHtml;
    grid.querySelectorAll(".reveal").forEach((el) => el.classList.add("is-visible"));
    grid.classList.remove("opacity-60");
    if (spinner) spinner.classList.add("hidden");
  }

  function updateUrl(q) {
    const url = new URL(window.location.href);
    if (q) url.searchParams.set("q", q);
    else url.searchParams.delete("q");
    window.history.replaceState(null, "", url.pathname + url.search);
  }

  let timer = null;
  let controller = null;

  async function runSearch(q) {
    if (controller) controller.abort();
    controller = new AbortController();
    grid.classList.add("opacity-60");
    if (spinner) spinner.classList.remove("hidden");

    const params = new URLSearchParams({ q });
    if (categoryInput && categoryInput.value) params.set("category", categoryInput.value);

    try {
      const res = await fetch(`/api/search/?${params}`, {
        signal: controller.signal,
        headers: { Accept: "application/json" },
      });
      if (!res.ok) throw new Error("search request failed");
      const data = await res.json();
      if (data.query !== q) return;

      grid.innerHTML = data.html;
      grid.classList.remove("opacity-60");
      if (spinner) spinner.classList.add("hidden");
      if (countEl) countEl.textContent = data.count;
      if (queryEl) queryEl.textContent = q;
      if (meta) meta.classList.remove("hidden");
      updateUrl(q);
    } catch (err) {
      if (err.name !== "AbortError") {
        grid.classList.remove("opacity-60");
        if (spinner) spinner.classList.add("hidden");
      }
    }
  }

  function clearSearch() {
    if (controller) controller.abort();
    clearTimeout(timer);
    input.value = "";
    restoreGrid();
    if (meta) meta.classList.add("hidden");
    updateUrl("");
    input.focus();
  }

  input.addEventListener("input", () => {
    clearTimeout(timer);
    const q = input.value.trim();
    if (!q) {
      clearSearch();
      return;
    }
    timer = setTimeout(() => runSearch(q), 250);
  });

  input.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && input.value) clearSearch();
  });

  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const q = input.value.trim();
      if (q) runSearch(q);
    });
  }

  if (clearBtn) clearBtn.addEventListener("click", (e) => {
    e.preventDefault();
    clearSearch();
  });
})();