document.querySelectorAll("[data-reveal]").forEach((section) => {
  const observer = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting) {
        section.classList.add("in");
        observer.disconnect();
      }
    },
    { threshold: 0.2 },
  );
  observer.observe(section);
});

const result = document.getElementById("result");
if (result) {
  result.scrollIntoView({ behavior: "smooth", block: "start" });
}

const form = document.querySelector(".diagnose-form");
if (form) {
  form.addEventListener("submit", () => {
    const btn = form.querySelector('button[type="submit"]');
    const fileInput = form.querySelector('input[name="video"]');
    const hasVideo = fileInput && fileInput.files && fileInput.files.length > 0;
    if (btn) {
      btn.disabled = true;
      btn.textContent = hasVideo ? "轉寫並診斷中…" : "診斷中…";
    }
  });
}
