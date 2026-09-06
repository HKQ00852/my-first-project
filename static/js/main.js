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
