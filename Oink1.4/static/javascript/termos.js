// Mostra os blocos [data-reveal] ao rolar. Suas animações dos slots entram aqui embaixo.
(function () {
  const itens = document.querySelectorAll("[data-reveal]");
  if (!("IntersectionObserver" in window)) { itens.forEach((e) => e.classList.add("visivel")); return; }
  const io = new IntersectionObserver((es) => es.forEach((e) => {
    if (e.isIntersecting) { e.target.classList.add("visivel"); io.unobserve(e.target); }
  }), { threshold: 0.12 });
  itens.forEach((e) => io.observe(e));
})();
