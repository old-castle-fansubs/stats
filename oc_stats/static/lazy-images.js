document.addEventListener("DOMContentLoaded", () => {
  const imageObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const image = entry.target;
        image.src = image.dataset.src;
        image.classList.remove("lazy");
        imageObserver.unobserve(image);
      }
    });
  });

  document.querySelectorAll(".lazy").forEach(image => {
    imageObserver.observe(image);
  });
});
