// Menu de acessibilidade presente em todas as telas: ouvir a tela, letra grande e alto contraste.
(function () {
  const app = document.querySelector('.app');
  const fundo = document.getElementById('acess-fundo');
  const abrir = document.getElementById('btn-acess');
  const ler = (k) => { try { return localStorage.getItem(k) === '1'; } catch (e) { return false; } };
  const gravar = (k, v) => { try { localStorage.setItem(k, v ? '1' : '0'); } catch (e) {} };

  // ---------- voz da leitura: usa a melhor voz em português que o aparelho tiver ----------
  // ordem: Francisca/Thalita (naturais do Edge) > outras naturais > Premium/Aprimorada (iPhone/Mac)
  //        > Google português (Chrome/Android) > Luciana/Felipe (iPhone) > qualquer pt-BR > qualquer pt
  const temVoz = 'speechSynthesis' in window;
  function nota(v) {
    const n = v.name, br = /pt[-_]br/i.test(v.lang);
    if (/francisca/i.test(n)) return 0;
    if (/thalita/i.test(n)) return 1;
    if (/natural|neural/i.test(n) && br) return 2;
    if (/premium|enhanced|aprimorad/i.test(n)) return 3;
    if (/google/i.test(n) && br) return 4;
    if (/luciana|felipe/i.test(n)) return 5;
    if (/online/i.test(n) && br) return 6;
    return br ? 7 : 8;
  }
  const vozesPt = () => (temVoz ? speechSynthesis.getVoices() : [])
    .filter((v) => v.lang && v.lang.toLowerCase().startsWith('pt')).sort((a, b) => nota(a) - nota(b));
  const lerVoz = () => { try { return localStorage.getItem('vitrine-voz') || ''; } catch (e) { return ''; } };
  function vozEscolhida() {
    const vs = vozesPt(), salva = lerVoz();
    return vs.find((v) => v.name === salva) || vs[0] || null;
  }

  // fala um texto em voz alta (pt-BR); devolve false se o navegador não tiver voz
  window.vitrineFala = function (texto, aoTerminar, voz) {
    if (!temVoz) return false;
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(texto);
    const v = voz || vozEscolhida();
    u.lang = v ? v.lang : 'pt-BR';
    if (v) u.voice = v;
    u.rate = v && nota(v) <= 3 ? 1 : 0.92; // as vozes naturais já falam num ritmo calmo
    if (aoTerminar) u.onend = aoTerminar;
    speechSynthesis.speak(u);
    return true;
  };

  // lista de vozes no menu de acessibilidade, para a pessoa testar e escolher
  const seletor = document.getElementById('voz-escolha');
  if (seletor && !temVoz) document.getElementById('opc-voz').hidden = true;
  if (seletor && temVoz) {
    const preenche = () => {
      const vs = vozesPt(); if (!vs.length) return;
      const salva = lerVoz();
      seletor.replaceChildren(new Option(`Automática (${vs[0].name.replace(/Microsoft |Online |\(Natural\)| - .*$/g, '').trim()})`, ''));
      vs.forEach((v) => seletor.add(new Option(v.name.replace(/^Microsoft /, '') + (nota(v) <= 3 ? ' ★' : ''), v.name)));
      seletor.value = vs.some((v) => v.name === salva) ? salva : '';
    };
    preenche(); speechSynthesis.addEventListener('voiceschanged', preenche);
    seletor.addEventListener('change', () => { try { localStorage.setItem('vitrine-voz', seletor.value); } catch (e) {} });
    document.getElementById('voz-testar').addEventListener('click', () =>
      window.vitrineFala('Olá! Esta é a voz que vai ler as lojas, os produtos e os preços para você.'));
  }

  function alternavel(id, classe, chave) {
    const b = document.getElementById(id);
    let ligado = ler(chave);
    const aplica = () => {
      app.classList.toggle(classe, ligado);
      b.setAttribute('aria-pressed', ligado ? 'true' : 'false');
      const est = b.querySelector('.est'); if (est) est.textContent = ligado ? 'Ligado' : 'Desligado';
    };
    b.addEventListener('click', () => { ligado = !ligado; gravar(chave, ligado); aplica(); });
    aplica();
  }
  alternavel('opc-letra', 'grande', 'vitrine-letra-grande');
  alternavel('opc-contraste', 'contraste', 'vitrine-alto-contraste');

  // "Ouvir esta tela": lê o texto de ajuda da página (atributo data-ouvir da seção principal)
  const ouvir = document.getElementById('opc-ouvir');
  ouvir.addEventListener('click', () => {
    const tela = document.querySelector('[data-ouvir]');
    const texto = tela ? tela.dataset.ouvir : 'Use os botões da barra de baixo: Comprar, Vender, Acessível e Ajuda.';
    fecha();
    if (!window.vitrineFala(texto)) alert(texto);
  });

  let focoAnterior;
  function abre() { focoAnterior = document.activeElement; fundo.classList.add('on'); ouvir.focus(); }
  function fecha() { fundo.classList.remove('on'); if (focoAnterior) focoAnterior.focus(); }
  document.querySelectorAll('.js-abre-acess').forEach((b) => b.addEventListener('click', abre));
  document.getElementById('acess-fechar').addEventListener('click', fecha);
  fundo.addEventListener('click', (e) => { if (e.target === fundo) fecha(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && fundo.classList.contains('on')) fecha(); });
  // ícones de linha (Lucide): troca cada <i data-lucide> pelo desenho em SVG
  if (window.lucide) lucide.createIcons();
})();

// Menu do topo: destaca a seção que está na tela (Comprar → Lojas → Como funciona)
(function () {
  const links = [...document.querySelectorAll('.cab-links a[data-secao]')];
  const secoes = links.map((a) => document.getElementById(a.dataset.secao)).filter(Boolean);
  if (secoes.length < 2) return; // só na página inicial
  const marca = (id) => links.forEach((a) => {
    const ativo = a.dataset.secao === id;
    a.classList.toggle('on', ativo);
    if (ativo) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current');
  });
  function atual() {
    const linha = 140; // logo abaixo do cabeçalho fixo
    let id = secoes[0].id;
    for (const s of secoes) {
      const bloco = s.closest('section, header') || s;
      if (bloco.getBoundingClientRect().top - linha <= 0) id = s.id;
    }
    // chegou ao fim da página: última seção do menu
    if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4) id = secoes[secoes.length - 1].id;
    marca(id);
  }
  links.forEach((a) => a.addEventListener('click', () => marca(a.dataset.secao)));
  let pendente = false;
  window.addEventListener('scroll', () => { if (!pendente) { pendente = true; requestAnimationFrame(() => { pendente = false; atual(); }); } }, { passive: true });
  atual();
})();
