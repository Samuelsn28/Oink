// Diálogos (sair, apagar conta) e olhinho da senha. Funciona sem JS também: o botão Sair faz logout direto.
(function () {
  const todos = (s) => document.querySelectorAll(s);

  function abrir(id) {
    const d = document.getElementById(id);
    if (!d || !d.showModal) return false;
    const g = d.querySelector("img[data-src]");
    if (g) g.src = g.dataset.src + "?v=" + Date.now();      // reinicia o GIF do Oink triste a cada abertura
    d.showModal();
    return true;
  }
  todos("[data-sair]").forEach((b) => b.addEventListener("click", (e) => { if (abrir("dlg-sair")) e.preventDefault(); }));
  todos("[data-abrir]").forEach((b) => b.addEventListener("click", () => abrir(b.dataset.abrir)));
  todos("[data-fechar]").forEach((b) => b.addEventListener("click", () => b.closest("dialog").close()));
  todos("dialog.dialogo").forEach((d) => d.addEventListener("click", (e) => {
    const r = d.getBoundingClientRect();                      // clicou fora da caixa = fechar
    if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) d.close();
  }));

  todos("input[type=password]").forEach((i) => {
    const w = document.createElement("span"); w.className = "senha-wrap";
    i.parentNode.insertBefore(w, i); w.appendChild(i);
    const b = document.createElement("button"); b.type = "button"; b.textContent = "Ver"; b.setAttribute("aria-label", "Mostrar senha");
    b.addEventListener("click", () => {
      const ver = i.type === "password"; i.type = ver ? "text" : "password";
      b.textContent = ver ? "Ocultar" : "Ver"; b.setAttribute("aria-label", ver ? "Ocultar senha" : "Mostrar senha");
    });
    w.appendChild(b);
  });
})();
