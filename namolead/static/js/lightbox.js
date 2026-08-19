(() => {
  const overlay = document.createElement("div");
  overlay.className = "lightbox";
  overlay.setAttribute("role", "dialog");
  overlay.setAttribute("aria-modal", "true");
  overlay.setAttribute("aria-label", "Image viewer");
  overlay.innerHTML = `
    <button type="button" class="lightbox-close" aria-label="Close image viewer">
      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12"/></svg>
    </button>
    <button type="button" class="lightbox-nav lightbox-prev" aria-label="Previous image">
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m15 18-6-6 6-6"/></svg>
    </button>
    <button type="button" class="lightbox-nav lightbox-next" aria-label="Next image">
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg>
    </button>
    <figure>
      <img alt="">
      <figcaption></figcaption>
    </figure>`;
  document.body.appendChild(overlay);

  const img = overlay.querySelector("img");
  const caption = overlay.querySelector("figcaption");
  const closeBtn = overlay.querySelector(".lightbox-close");
  const prevBtn = overlay.querySelector(".lightbox-prev");
  const nextBtn = overlay.querySelector(".lightbox-next");

  let items = [];
  let index = 0;
  let lastTrigger = null;

  function show(i) {
    index = (i + items.length) % items.length;
    const trigger = items[index];
    img.src = trigger.dataset.lightboxSrc || trigger.currentSrc || trigger.src;
    img.alt = trigger.getAttribute("aria-label") || "";
    const cap = trigger.dataset.lightboxCaption || trigger.alt || "";
    caption.textContent = cap;
    caption.hidden = !cap;
    const multi = items.length > 1;
    prevBtn.hidden = !multi;
    nextBtn.hidden = !multi;
  }

  function open(trigger) {
    lastTrigger = trigger;
    const group = trigger.dataset.lightboxGroup;
    items = group
      ? [...document.querySelectorAll(`[data-lightbox-group="${group}"]`)]
      : [trigger];
    show(items.indexOf(trigger));
    overlay.classList.add("is-open");
    closeBtn.focus();
    document.body.style.overflow = "hidden";
  }

  function closeLightbox() {
    overlay.classList.remove("is-open");
    document.body.style.overflow = "";
    if (lastTrigger) lastTrigger.focus();
  }

  document.addEventListener("click", (e) => {
    const trigger = e.target.closest("[data-lightbox]");
    if (!trigger) return;
    e.preventDefault();
    e.stopPropagation();
    open(trigger);
  });

  closeBtn.addEventListener("click", closeLightbox);
  prevBtn.addEventListener("click", (e) => { e.stopPropagation(); show(index - 1); });
  nextBtn.addEventListener("click", (e) => { e.stopPropagation(); show(index + 1); });
  overlay.addEventListener("click", (e) => {
    if (!e.target.closest("button, img")) closeLightbox();
  });

  document.addEventListener("keydown", (e) => {
    if (!overlay.classList.contains("is-open")) return;
    if (e.key === "Escape") { e.preventDefault(); closeLightbox(); }
    else if (e.key === "ArrowLeft") { e.preventDefault(); show(index - 1); }
    else if (e.key === "ArrowRight") { e.preventDefault(); show(index + 1); }
  });
})();