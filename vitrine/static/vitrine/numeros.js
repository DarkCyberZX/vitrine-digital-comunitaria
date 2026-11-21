/* Números da abertura: os cartões sobem um a um e os valores contam até o número real.
   Leitores de tela ouvem só o valor final; quem pede menos movimento vê tudo parado. */
(function () {
  const lista = document.querySelector('.hero .numeros');
  if (!lista) return;
  const calmo = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const valores = [...lista.querySelectorAll('b')].map((b) => {
    const txt = b.textContent.trim();
    const m = txt.match(/^(\d+)(?:,(\d+))?$/);
    if (!m) return null;                       // "Grátis" não conta, só aparece
    const fim = parseFloat(txt.replace(',', '.'));
    const casas = m[2] ? m[2].length : 0;
    const voz = document.createElement('span');  // valor final para leitor de tela
    voz.className = 'sr-only'; voz.textContent = txt;
    b.setAttribute('aria-hidden', 'true'); b.after(voz);
    return { b, fim, casas, txt };
  });
  if (calmo) return;
  const escreve = (v, n) => v.b.textContent = n.toFixed(v.casas).replace('.', ',');
  valores.forEach((v) => v && escreve(v, 0));
  lista.classList.add('numeros-anima');
  const inicia = () => {
    lista.classList.add('numeros-entra');
    const t0 = performance.now(), dur = 1400;
    const passo = (t) => {
      const p = Math.min(1, (t - t0) / dur), suave = 1 - Math.pow(1 - p, 3);
      valores.forEach((v) => v && escreve(v, v.fim * suave));
      if (p < 1) requestAnimationFrame(passo);
      else valores.forEach((v) => v && (v.b.textContent = v.txt));
    };
    setTimeout(() => requestAnimationFrame(passo), 250);
  };
  if ('IntersectionObserver' in window) {
    const ob = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) { ob.disconnect(); inicia(); } }, { threshold: 0.4 });
    ob.observe(lista);
  } else inicia();
})();
