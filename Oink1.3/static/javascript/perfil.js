// Recorte da foto de perfil: arraste para posicionar, use o zoom, e a foto sai quadrada 400x400.
(function () {
  const input = document.getElementById("id_foto"), dlg = document.getElementById("dlg-recorte");
  if (!input || !dlg) return;
  const cv = document.getElementById("recorte-canvas"), ctx = cv.getContext("2d");
  const zoom = document.getElementById("recorte-zoom"), previa = document.getElementById("previa");
  const T = cv.width; let img = null, base = 1, ox = 0, oy = 0, z = 1, arrasto = null;

  function limitar() {
    const w = img.width * base * z, h = img.height * base * z;
    ox = Math.min(0, Math.max(T - w, ox)); oy = Math.min(0, Math.max(T - h, oy));
  }
  function desenhar(c, t, mascara) {
    const k = t / T; c.clearRect(0, 0, t, t);
    c.drawImage(img, ox * k, oy * k, img.width * base * z * k, img.height * base * z * k);
    if (!mascara) return;
    c.save(); c.fillStyle = "rgba(8,8,32,.62)"; c.beginPath(); c.rect(0, 0, t, t);
    c.arc(t / 2, t / 2, t / 2 - 6, 0, Math.PI * 2, true); c.fill("evenodd");
    c.strokeStyle = "#5b14f0"; c.lineWidth = 3; c.beginPath(); c.arc(t / 2, t / 2, t / 2 - 6, 0, Math.PI * 2); c.stroke(); c.restore();
  }
  const render = () => { limitar(); desenhar(ctx, T, true); };

  function abrirImagem(file) {
    const url = URL.createObjectURL(file), i = new Image();
    i.onload = () => {
      img = i; base = Math.max(T / i.width, T / i.height); z = 1; zoom.value = 1;
      ox = (T - i.width * base) / 2; oy = (T - i.height * base) / 2; render(); dlg.showModal(); URL.revokeObjectURL(url);
    };
    i.onerror = () => { alert("Não consegui abrir essa imagem. Use JPG, PNG ou WEBP."); input.value = ""; };
    i.src = url;
  }
  input.addEventListener("change", () => { const f = input.files[0]; if (f) abrirImagem(f); });

  zoom.addEventListener("input", () => {
    const cx = (T / 2 - ox) / (base * z), cy = (T / 2 - oy) / (base * z);   // mantém o centro no lugar
    z = parseFloat(zoom.value); ox = T / 2 - cx * base * z; oy = T / 2 - cy * base * z; render();
  });
  cv.addEventListener("pointerdown", (e) => { arrasto = { x: e.clientX, y: e.clientY, ox, oy }; cv.setPointerCapture(e.pointerId); });
  cv.addEventListener("pointermove", (e) => {
    if (!arrasto) return; const k = T / cv.getBoundingClientRect().width;
    ox = arrasto.ox + (e.clientX - arrasto.x) * k; oy = arrasto.oy + (e.clientY - arrasto.y) * k; render();
  });
  ["pointerup", "pointercancel"].forEach((ev) => cv.addEventListener(ev, () => { arrasto = null; }));
  cv.addEventListener("wheel", (e) => {
    e.preventDefault(); zoom.value = Math.min(3, Math.max(1, parseFloat(zoom.value) - e.deltaY / 500)); zoom.dispatchEvent(new Event("input"));
  }, { passive: false });

  document.getElementById("recorte-ok").addEventListener("click", () => {
    const out = document.createElement("canvas"); out.width = out.height = 400; desenhar(out.getContext("2d"), 400, false);
    out.toBlob((b) => {
      const dt = new DataTransfer(); dt.items.add(new File([b], "foto.jpg", { type: "image/jpeg" }));
      input.files = dt.files; previa.src = URL.createObjectURL(b);
      const rm = document.getElementById("id_remover_foto"); if (rm) rm.checked = false;
      dlg.close();
    }, "image/jpeg", 0.9);
  });
  document.getElementById("recorte-cancelar").addEventListener("click", () => { input.value = ""; dlg.close(); });
  dlg.addEventListener("cancel", () => { input.value = ""; });
})();
