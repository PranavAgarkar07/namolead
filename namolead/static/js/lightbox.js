(() => {
  const overlay = document.createElement("div");
  overlay.className = "lightbox";
  overlay.setAttribute("role", "dialog");
  overlay.setAttribute("aria-modal", "true");
  overlay.setAttribute("aria-label", "Image viewer");
  overlay.innerHTML = `
    <button type="button" class="lightbox-close" aria-label="Close image viewer">
      <i class="fa-solid fa-xmark" aria-hidden="true"></i>
    </button>
    <button type="button" class="lightbox-nav lightbox-prev" aria-label="Previous image">
      <i class="fa-solid fa-chevron-left" aria-hidden="true"></i>
    </button>
    <button type="button" class="lightbox-nav lightbox-next" aria-label="Next image">
      <i class="fa-solid fa-chevron-right" aria-hidden="true"></i>
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