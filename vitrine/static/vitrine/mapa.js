// Tela inicial: busca, categorias, filtros, mapa e lista das bancas.
// Os dados vêm do Django via json_script; os cartões são montados com createElement (nada de innerHTML com dados).
(function () {
  const BANCAS = JSON.parse(document.getElementById('dados-bancas').textContent);
  const $ = (s) => document.querySelector(s);
  const fmt = (v) => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  const num1 = (v) => v.toFixed(1).replace('.', ',');
  const PULA = new Set(['de', 'do', 'da', 'dos', 'das', 'd', 'e', 'o', 'a', 'os', 'as', 'um', 'uma', 'seu', 'sua', 'dona', 'dono', 'sr', 'sra', 'no', 'na', 'nos', 'nas', 'em', 'com', 'pra', 'para', 'por', 'loja']);
  // separa em palavras sem acento; na pergunta, ignora palavras pequenas de ligação
  const palavras = (t, tudo) => semAcento(t).split(/[^a-z0-9]+/).filter((w) => w && (tudo || !PULA.has(w)));
  const semAcento = (t) => t.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
    let grupo = null, mapa, marcadores = [], marcaVoce, circulo, busca = '', perto = null, origem = '';

  function toast(msg) {
    const t = $('#toast'); t.textContent = msg; t.classList.add('on');
    clearTimeout(t._t); t._t = setTimeout(() => t.classList.remove('on'), 2600);
  }
  function el(tag, attrs = {}, ...filhos) {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === 'style') e.style.cssText = v; else if (k === 'class') e.className = v; else e.setAttribute(k, v);
    }
    filhos.flat().forEach((f) => { if (f != null && f !== false) e.append(f instanceof Node ? f : document.createTextNode(String(f))); });
    return e;
  }
  function dist(a, b) {
    const R = 6371, r = Math.PI / 180, dLat = (b.lat - a.lat) * r, dLng = (b.lng - a.lng) * r;
    const x = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(dLng / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(x));
  }
  const icone = (nome) => el('i', { 'data-lucide': nome, class: 'ic-l', 'aria-hidden': 'true' });
  const desenhaIcones = () => { if (window.lucide) lucide.createIcons(); };
  const distTexto = (km) => (km < 1 ? Math.round(km * 1000) + ' m' : km.toFixed(1).replace('.', ',') + ' km');

  // estrelas: visual escondido do leitor de tela + texto "Nota 4,8 de 5"
  function estrelas(media, n) {
    const box = el('span', { class: 'nota' });
    if (media == null) { box.append(el('span', { class: 'nota-sem' }, 'Ainda sem avaliações')); return box; }
    const vis = el('span', { class: 'estrelas', 'aria-hidden': 'true' });
    for (let i = 1; i <= 5; i++) vis.append(el('span', { class: media >= i - 0.25 ? 'e cheia' : media >= i - 0.75 ? 'e meia' : 'e' }, '★'));
    box.append(el('b', {}, num1(media)), vis, el('span', { class: 'nota-n' }, `(${n} ${n === 1 ? 'avaliação' : 'avaliações'})`),
      el('span', { class: 'sr-only' }, `Nota ${num1(media)} de 5`));
    return box;
  }

  // ---------- filtros ----------
  const form = $('#form-filtros');
  function lerFiltros() {
    const f = new FormData(form);
    return { cats: f.getAll('cat'), ordem: f.get('ordem'), aberta: f.has('aberta'), pronta: f.has('pronta'), preco: f.get('preco'),
      nota: f.get('nota') ? parseFloat(f.get('nota')) : null, bairros: f.getAll('bairro'), km: f.get('km') ? parseFloat(f.get('km')) : null };
  }
  function contaFiltros(f) {
    return f.cats.length + (f.aberta ? 1 : 0) + (f.pronta ? 1 : 0) + (f.preco ? 1 : 0) + (f.nota ? 1 : 0) + f.bairros.length + (f.km && perto ? 1 : 0);
  }

  function filtradas() {
    const f = lerFiltros(), q = semAcento(busca.trim());
    let l = BANCAS.filter((b) => !f.cats.length || f.cats.includes(b.cat));
    let parecidos = false;
    if (q) {
      // busca por palavras: "coco do seu Zé" procura "coco" e "ze" (ignora do, da, seu, dona...)
      const termos = palavras(q);
      const comeca = (texto, t) => palavras(texto, true).some((w) => w.startsWith(t));
      l = l.map((b) => {
        let pontos = 0, casou = 0;
        const achados = new Set();
        for (const t of termos) {
          const noProduto = b.produtos.filter((n, i) => comeca(n + ' ' + ((b.pdesc || [])[i] || ''), t));
          const peso = comeca(b.nome + ' ' + b.resp, t) ? 4 : comeca(b.cat_nome, t) ? 3
            : comeca([b.bairro, b.ponto, b.cep].join(' '), t) ? 2 : noProduto.length ? 1 : 0;
          if (peso) { casou++; pontos += peso; }
          noProduto.forEach((n) => achados.add(n));
        }
        return { ...b, pontos, casou, achados: [...achados] };
      });
      const todas = l.filter((b) => termos.length && b.casou === termos.length);
      // se nenhuma loja tem todas as palavras, mostra as que têm alguma
      if (todas.length || !termos.length) l = todas; else { l = l.filter((b) => b.casou > 0); parecidos = l.length > 0; }
    }
    if (f.aberta) l = l.filter((b) => b.aberta);
    if (f.pronta) l = l.filter((b) => b.pronta);
    if (f.preco === 'ate10') l = l.filter((b) => b.menor != null && b.menor <= 10);
    if (f.preco === '10a50') l = l.filter((b) => b.menor != null && b.menor >= 10 && b.menor <= 50);
    if (f.preco === 'mais50') l = l.filter((b) => b.menor != null && b.menor > 50);
    if (f.nota) l = l.filter((b) => b.media != null && b.media >= f.nota);
    if (f.bairros.length) l = l.filter((b) => f.bairros.includes(b.bairro));
    const ref = perto; // só existe se a pessoa compartilhou a localização
    if (ref) l = l.map((b) => ({ ...b, km: dist(ref, b) }));
    // distância máxima: só vale quando a pessoa compartilhou a localização
    if (f.km && perto) l = l.filter((b) => b.km <= f.km);
    let ordem;
    if (f.ordem === 'perto' && perto) ordem = (a, b) => a.km - b.km;
    else if (f.ordem === 'preco') ordem = (a, b) => (a.menor ?? 1e9) - (b.menor ?? 1e9);
    else ordem = (a, b) => (b.media ?? 0) - (a.media ?? 0) || b.n_aval - a.n_aval;
    // com busca, primeiro as lojas mais relevantes; depois a ordem escolhida
    l.sort((a, b) => (q ? (b.casou - a.casou) || (b.pontos - a.pontos) : 0) || ordem(a, b));
    return { l, f, parecidos };
  }

  function cartao(b) {
    const foto = b.foto ? el('img', { class: 'cb-foto', src: b.foto, alt: '', loading: 'lazy' })
      : el('div', { class: 'cb-foto', style: `background:${b.cor}`, 'aria-hidden': 'true' }, icone(b.icone));
    const local = `${b.bairro} • ${b.ponto}` + (b.km != null ? ` • ${distTexto(b.km)}` : '');
    const preco = `${b.qtd} produtos` + (b.menor != null ? ` • a partir de ${fmt(b.menor)}` : '');
    const selos = el('div', { class: 'selos' },
      el('span', { class: 'selo ' + (b.aberta ? 'aberto' : 'fechado') }, b.aberta ? '● Aberto agora' : 'Fechado'),
      b.pronta && el('span', { class: 'selo pronta-s' }, icone('check'), ' Pronta entrega'));
    return el('a', { class: 'cartao-banca', href: b.url },
      foto,
      el('div', { class: 'cb-corpo' },
        el('h3', {}, b.nome), estrelas(b.media, b.n_aval),
        el('p', { class: 'cb-local' }, local), el('p', { class: 'cb-preco' }, preco),
        b.horario ? el('p', { class: 'cb-horario' }, icone('clock-3'), ' ', b.horario) : null,
        b.achados && b.achados.length ? el('p', { class: 'cb-achou' }, icone('search'), ' Tem: ', el('b', {}, b.achados.join(', '))) : null,
        b.trecho && el('blockquote', { class: 'cb-trecho' }, `“${b.trecho}”`),
        selos));
  }

  const POR_VEZ = 10;
  let limite = POR_VEZ, ultimaChave = null;

  function desenha() {
    const { l, f } = filtradas();
    $('#qtd').textContent = l.length + (l.length === 1 ? ' loja encontrada' : ' lojas encontradas');
    const n = contaFiltros(f); $('#n-filtros').textContent = n ? n : '';
    $('#f-aplicar').textContent = `Ver ${l.length} ${l.length === 1 ? 'loja' : 'lojas'}`;
    const lista = $('#lista'); lista.replaceChildren();
    if (!l.length) lista.append(el('div', { class: 'vazio' }, 'Nenhuma loja com esses filtros. ', el('button', { type: 'button', class: 'link-limpar', id: 'limpar-vazio' }, 'Limpar filtros')));
    // mostra as 10 primeiras (as mais bem avaliadas, ou conforme a ordem escolhida) e o botão "Ver mais"
    const chave = JSON.stringify([f, busca, perto && [perto.lat, perto.lng]]);
    if (chave !== ultimaChave) { limite = POR_VEZ; ultimaChave = chave; }
    const antes = lista.childElementCount;
    l.slice(0, limite).forEach((b) => lista.append(cartao(b)));
    if (l.length > limite) {
      const bt = el('button', { type: 'button', class: 'btn-ver-mais', id: 'ver-mais' },
        'Ver mais lojas');
      bt.addEventListener('click', () => {
        const proxima = limite; limite += POR_VEZ; desenha();
        const c = lista.querySelectorAll('.cartao-banca')[proxima + antes]; if (c) c.focus();
      });
      lista.append(el('div', { class: 'ver-mais-caixa' },
        el('p', { class: 'ver-mais-txt' }, `Mostrando ${limite} de ${l.length} lojas`), bt));
    }
    desenhaIcones();
    const lv = $('#limpar-vazio'); if (lv) lv.addEventListener('click', limpar);
    if (mapa) {
      if (grupo) grupo.clearLayers(); else marcadores.forEach((m) => m.remove());
      marcadores = [];
      l.forEach((b) => {
        const pop = el('div', {}, el('strong', {}, b.nome), el('br'), b.media != null ? `★ ${num1(b.media)} • ` : '', b.km != null && perto ? el('span', {}, `${distTexto(b.km)} de você • `) : '', el('a', { href: b.url, style: 'color:#0f766e' }, 'Ver produtos →'));
        const icone = L.divIcon({ className: '', html: `<div class="pino" style="background:${b.aberta ? 'var(--verde)' : '#64748b'}"><i data-lucide="${b.icone}" class="ic-l"></i></div>`, iconSize: [36, 36], iconAnchor: [18, 36], popupAnchor: [0, -34] });
        const m = L.marker([b.lat, b.lng], { icon: icone, title: b.nome }).bindPopup(pop);
        marcadores.push(m);
        if (!grupo) m.addTo(mapa);
      });
      if (grupo) grupo.addLayers(marcadores);
      desenhaIcones();
      // sem busca nem filtro: abre na região com mais lojas (orla e centro); com busca, mostra só os resultados
      const semFiltro = !busca.trim() && !contaFiltros(f);
      if (circulo) { circulo.remove(); circulo = null; }
      if (perto && f.km) circulo = L.circle([perto.lat, perto.lng], { radius: f.km * 1000, color: '#0f766e', weight: 2, fillOpacity: 0.06, interactive: false }).addTo(mapa);
      if (perto && f.km) mapa.fitBounds(circulo.getBounds(), { padding: [10, 10] });
      else if (semFiltro && !perto) mapa.setView([-9.6585, -35.7200], window.innerWidth < 768 ? 13 : 14);
      else if (l.length && !perto && !f.km) mapa.fitBounds(L.latLngBounds(l.map((b) => [b.lat, b.lng])).pad(0.15), { maxZoom: 16 });
    }
  }

  function limpar() {
    form.reset(); busca = ''; esqueceLocal(); $('#campo-busca').value = ''; atualizaDica();
    desenha();
  }

  // ---------- gaveta de filtros (celular) ----------
  const painel = $('#filtros'), btnF = $('#btn-filtros');
  // fundo escuro: tocar fora fecha a gaveta
  const fundoF = document.createElement('div'); fundoF.className = 'filtros-fundo'; document.body.append(fundoF);
  const tituloF = painel.querySelector('.filtros-topo b'); tituloF.tabIndex = -1;
  const celular = () => !window.matchMedia('(min-width:1024px)').matches;
  const abreF = () => {
    painel.classList.add('aberta'); fundoF.classList.add('on'); btnF.setAttribute('aria-expanded', 'true');
    if (celular()) document.documentElement.classList.add('trava-rolagem'); // a página de trás não rola junto
    painel.scrollTop = 0; tituloF.focus({ preventScroll: true }); // foco no título: não abre o seletor nem marca campo
  };
  const fechaF = () => {
    painel.classList.remove('aberta'); fundoF.classList.remove('on'); btnF.setAttribute('aria-expanded', 'false');
    document.documentElement.classList.remove('trava-rolagem'); btnF.focus({ preventScroll: true });
  };
  fundoF.addEventListener('click', fechaF);
  btnF.addEventListener('click', abreF);
  $('#filtros-fechar').addEventListener('click', fechaF);
  $('#f-aplicar').addEventListener('click', () => { fechaF(); $('.bancas-sec').scrollIntoView({ behavior: 'smooth' }); });
  $('#f-limpar').addEventListener('click', limpar);
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && painel.classList.contains('aberta')) fechaF(); });
  form.addEventListener('change', desenha);

  // ---------- mapa ----------
  if (window.L) {
    mapa = L.map('mapa', { zoomControl: true, scrollWheelZoom: false }).setView([-9.6655, -35.707], 14);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap' }).addTo(mapa);
    // lojas próximas viram uma bolinha com o número; tocar ou dar zoom abre o grupo
    if (L.markerClusterGroup) {
      grupo = L.markerClusterGroup({
        maxClusterRadius: 32, showCoverageOnHover: false, spiderfyOnMaxZoom: true, chunkedLoading: true,
        iconCreateFunction: (c) => {
          const n = c.getChildCount();
          return L.divIcon({ html: `<div class="grupo-pino"><b>${n}</b><span>lojas</span></div>`, className: '', iconSize: [42, 42], iconAnchor: [21, 21] });
        },
      }).addTo(mapa);
      grupo.on('animationend spiderfied', desenhaIcones);
      mapa.on('zoomend moveend', desenhaIcones);
    }
    // rodinha do mouse: liga depois de clicar no mapa (quem só está rolando a página não fica preso no zoom)
    const caixaMapa = mapa.getContainer();
    const avisoRoda = el('div', { class: 'mapa-aviso', 'aria-hidden': 'true' }, 'Clique no mapa para usar a rodinha do mouse');
    caixaMapa.append(avisoRoda);
    mapa.on('click focus', () => { mapa.scrollWheelZoom.enable(); avisoRoda.classList.remove('on'); });
    caixaMapa.addEventListener('mouseleave', () => mapa.scrollWheelZoom.disable());
    caixaMapa.addEventListener('wheel', () => {
      if (mapa.scrollWheelZoom.enabled()) return;
      avisoRoda.classList.add('on'); clearTimeout(avisoRoda._t); avisoRoda._t = setTimeout(() => avisoRoda.classList.remove('on'), 1600);
    }, { passive: true });
    // botão dentro do mapa: centraliza em você (pede a localização se ainda não tiver)
    const Centraliza = L.Control.extend({ options: { position: 'topleft' }, onAdd() {
      const bt = L.DomUtil.create('button', 'mapa-eu');
      bt.type = 'button'; bt.title = 'Centralizar em mim'; bt.setAttribute('aria-label', 'Centralizar o mapa em mim');
      bt.innerHTML = '<i data-lucide="locate-fixed" class="ic-l" aria-hidden="true"></i>';
      L.DomEvent.disableClickPropagation(bt);
      bt.addEventListener('click', () => { if (perto) mapa.setView([perto.lat, perto.lng], 16); else pedeGps(); });
      return bt;
    } });
    new Centraliza().addTo(mapa);
    desenhaIcones();
  } else {
    $('#mapa').append(el('div', { class: 'vazio' }, 'Mapa indisponível sem internet.'));
  }

  // busca: filtra a lista e avisa logo abaixo do campo quantas lojas foram encontradas
  const dica = $('#busca-dica');
  const irParaResultados = () => $('.bancas-sec').scrollIntoView({ behavior: 'smooth', block: 'start' });
  function atualizaDica() {
    const termo = busca.trim();
    if (!termo) { dica.replaceChildren(); dica.classList.remove('on'); return; }
    const { l: achadas, parecidos } = filtradas(); const n = achadas.length;
    const ver = el('button', { type: 'button', class: 'dica-ver' }, 'Ver resultados ', icone('arrow-down'));
    ver.addEventListener('click', irParaResultados);
    dica.replaceChildren(
      !n ? `Nenhuma loja para “${termo}”. Tente outra palavra. `
        : parecidos ? `Nenhuma loja tem tudo de “${termo}”. Mostrando ${n} ${n === 1 ? 'parecida' : 'parecidas'}. `
        : `${n} ${n === 1 ? 'loja encontrada' : 'lojas encontradas'} para “${termo}”. `,
      n ? ver : '');
    dica.classList.add('on'); desenhaIcones();
  }
  $('#campo-busca').addEventListener('input', (e) => { busca = e.target.value; desenha(); atualizaDica(); });
  // exemplos de busca: tocar em um exemplo já pesquisa
  document.querySelectorAll('.busca-ex').forEach((bt) => bt.addEventListener('click', () => {
    const c = $('#campo-busca'); c.value = bt.dataset.busca; busca = c.value; desenha(); atualizaDica();
  }));
  // os outros exemplos ficam nos botões "Experimente" (nada se mexe sozinho na tela)
  $('#form-busca').addEventListener('submit', (e) => { e.preventDefault(); busca = $('#campo-busca').value; desenha(); atualizaDica(); irParaResultados(); });

  // ---------- sua localização (só pelo GPS, quando a pessoa permite) ----------
  const status = $('#local-status'), dicaKm = $('#f-km-dica');
  function usaLocal(lat, lng, como, rolar) {
    perto = { lat, lng }; origem = como; $('#f-ordem').value = 'perto';
    if (mapa) {
      if (marcaVoce) marcaVoce.remove();
      marcaVoce = L.marker([lat, lng], { title: 'Você está aqui', interactive: false, keyboard: false, icon: L.divIcon({ className: '', html: '<div class="voce"></div>', iconSize: [18, 18], iconAnchor: [9, 9] }) }).addTo(mapa);
      mapa.setView([lat, lng], 15);
    }
    status.textContent = como; status.classList.add('ok'); dicaKm.hidden = true;
    desenha();
    if (rolar) $('.bancas-sec').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  function esqueceLocal() {
    perto = null; origem = '';
    if (marcaVoce) { marcaVoce.remove(); marcaVoce = null; }
    status.textContent = 'Use sua localização ou digite um endereço para ver a distância até cada loja.'; status.classList.remove('ok'); dicaKm.hidden = false;
  }
  function pedeGps(rolar) {
    // sem permissão (ou se o GPS falhar): não inventa um lugar; pede o endereço ou o CEP
    const semLocal = (negou) => {
      status.textContent = negou ? 'Você não compartilhou sua localização, então a distância não aparece.' : 'Não conseguimos achar sua localização agora. Tente de novo.';
      status.classList.remove('ok');
      if ($('#f-ordem').value === 'perto') { $('#f-ordem').value = 'nota'; desenha(); }
      toast(negou ? 'Sem a localização: digite um endereço ou CEP nos filtros' : 'Não conseguimos achar sua localização');
    };
    if (!navigator.geolocation) return semLocal(false);
    status.textContent = 'Procurando onde você está…';
    navigator.geolocation.getCurrentPosition((p) => {
      usaLocal(p.coords.latitude, p.coords.longitude, 'Usando a sua localização atual.', rolar);
      toast('Mostrando a distância até cada loja');
    }, (erro) => semLocal(!!erro && erro.code === 1), { timeout: 8000 });
  }
  // escolher "Mais perto de mim" sem ter dado a localização: pede a localização
  $('#f-ordem').addEventListener('change', () => { if ($('#f-ordem').value === 'perto' && !perto) pedeGps(false); });
  $('#btn-gps').addEventListener('click', () => pedeGps(true));

  // ---------- ou um endereço / CEP digitado (sem GPS) ----------
  const campoEnd = $('#f-endereco');
  async function usaEndereco() {
    const txt = campoEnd.value.trim();
    if (txt.length < 3) { status.textContent = 'Digite o nome da rua, do bairro ou o CEP.'; status.classList.remove('ok'); campoEnd.focus(); return; }
    // se não achar, não deixa valendo um endereço antigo
    const falha = (msg) => { if (perto) { esqueceLocal(); if ($('#f-ordem').value === 'perto') $('#f-ordem').value = 'nota'; desenha(); } status.textContent = msg; };
    status.classList.remove('ok'); status.textContent = 'Procurando o endereço…';
    const q = new URLSearchParams({ format: 'json', limit: '1', countrycodes: 'br' });
    let nome = txt;
    const d = txt.replace(/\D/g, '');
    try {
      if (/^\s*\d{5}-?\d{3}\s*$/.test(txt)) {
        const e = await (await fetch(`https://viacep.com.br/ws/${d}/json/`)).json();
        if (e.erro) { falha('CEP não encontrado. Confira os números.'); return; }
        if (e.localidade !== 'Maceió') { falha(`Esse CEP é de ${e.localidade}. A Vitrine, por enquanto, é só de Maceió.`); return; }
        nome = [e.logradouro, e.bairro].filter(Boolean).join(', ') || txt;
        q.set('q', [e.logradouro, e.bairro, 'Maceió, Alagoas'].filter(Boolean).join(', '));
      } else {
        q.set('q', /macei[oó]/i.test(txt) ? txt : `${txt}, Maceió, Alagoas`);
      }
      // só aceita resultados dentro de Maceió
      q.set('viewbox', '-35.85,-9.40,-35.60,-9.75'); q.set('bounded', '1');
      const [achou] = await (await fetch('https://nominatim.openstreetmap.org/search?' + q, { headers: { 'Accept-Language': 'pt-BR' } })).json();
      if (!achou) { falha('Não achamos esse endereço em Maceió. Tente o nome da rua com o bairro, ou o CEP.'); return; }
      fechaFiltrosSePrecisar();
      usaLocal(parseFloat(achou.lat), parseFloat(achou.lon), `Usando o endereço: ${nome}.`, true);
      toast('Mostrando a distância a partir desse endereço');
    } catch (err) {
      falha('Não deu para procurar o endereço agora. Tente de novo.');
    }
  }
  function fechaFiltrosSePrecisar() { const f = $('#filtros-fechar'); if (f && window.innerWidth < 768 && f.offsetParent) f.click(); }
  $('#f-endereco-ok').addEventListener('click', usaEndereco);
  campoEnd.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); usaEndereco(); } });
  $('#f-gps').addEventListener('click', () => pedeGps(false));


  desenha();
})();
