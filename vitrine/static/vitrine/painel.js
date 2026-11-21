// Painel do comerciante: cadastro por voz (Web Speech API) e aviso do Pix.
(function () {
  const $ = (s) => document.querySelector(s);
  const campoNome = $('#id_p-nome'), campoPreco = $('#id_p-preco'), campoVoz = $('#id_p-cadastrado_por_voz');

  function toast(msg) {
    const t = $('#toast'); t.textContent = msg; t.classList.add('on');
    clearTimeout(t._t); t._t = setTimeout(() => t.classList.remove('on'), 2600);
  }

  // ---- números falados -> valor ----
  const NUM = { zero: 0, um: 1, uma: 1, dois: 2, duas: 2, 'três': 3, tres: 3, quatro: 4, cinco: 5, seis: 6, sete: 7, oito: 8, nove: 9, dez: 10,
    onze: 11, doze: 12, treze: 13, quatorze: 14, catorze: 14, quinze: 15, dezesseis: 16, dezessete: 17, dezoito: 18, dezenove: 19,
    vinte: 20, trinta: 30, quarenta: 40, cinquenta: 50, sessenta: 60, setenta: 70, oitenta: 80, noventa: 90, cem: 100, cento: 100,
    duzentos: 200, trezentos: 300, quatrocentos: 400, quinhentos: 500 };
  function paraNumero(txt) {
    let total = 0, achou = false;
    for (const w of txt.split(/\s+/)) {
      if (w === 'e' || !w) continue;
      if (NUM[w] != null) { total += NUM[w]; achou = true; }
      else if (/^\d+([.,]\d+)?$/.test(w)) { total += parseFloat(w.replace(',', '.')); achou = true; }
    }
    return achou ? total : null;
  }
  // "tapioca de queijo, oito reais e cinquenta" | "bolo de milho 12 reais" | "cocada 4,50"
  function interpreta(frase) {
    const f = frase.toLowerCase().replace(/r\$\s*/g, '').trim();
    const m = f.match(/^(.*?)[,\s]+(?:por\s+|a\s+|custa\s+)?([\d.,a-zçãéêíóôú\s]+?)\s*(?:reais|real|conto|contos)(?:\s+e\s+(.+?)(?:\s+centavos)?)?$/);
    if (m) {
      // separa o nome do valor: o valor começa na primeira palavra que é número
      const palavras = (m[1] + ' ' + m[2]).split(/\s+/);
      const i = palavras.findIndex((w) => NUM[w] != null || /^\d/.test(w));
      const nome = palavras.slice(0, i).join(' ').replace(/[,.]$/, '');
      const reais = paraNumero(palavras.slice(i).join(' '));
      const cent = m[3] ? paraNumero(m[3]) || 0 : 0;
      if (i > 0 && reais != null) return { nome, preco: reais + cent / 100 };
    }
    const n = f.match(/^(.*?)[,\s]+(\d+(?:[.,]\d{1,2})?)$/);
    if (n) return { nome: n[1].trim(), preco: parseFloat(n[2].replace(',', '.')) };
    return { nome: f, preco: null };
  }
  function preenche(frase) {
    const o = $('#ouvido'); o.textContent = '“' + frase + '”'; o.classList.add('tem');
    const r = interpreta(frase);
    if (r.nome) campoNome.value = r.nome.charAt(0).toUpperCase() + r.nome.slice(1);
    if (r.preco != null) campoPreco.value = r.preco.toFixed(2).replace('.', ',');
    campoVoz.value = 'True';
    toast(r.preco != null ? 'Entendi! Confira e coloque na vitrine' : 'Entendi o produto. Falta o preço');
    // repete em voz alta o que entendeu, para quem tem dificuldade de leitura
    if (window.vitrineFala) {
      const preco = r.preco != null ? `, ${r.preco.toFixed(2).replace('.', ',')} reais` : '. Faltou o preço, fale de novo';
      window.vitrineFala(`Entendi: ${r.nome}${preco}. Se estiver certo, toque em colocar na vitrine.`);
    }
  }

  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  let rec, ouvindo = false;
  // foto do produto: mostra a prévia antes de enviar
  const campoFoto = $('#id_p-imagem');
  if (campoFoto) campoFoto.addEventListener('change', () => {
    const f = campoFoto.files[0], previa = $('#foto-previa');
    if (!f) return;
    if (f.size > 5 * 1024 * 1024) { toast('Foto grande demais. Use uma de até 5 MB'); campoFoto.value = ''; return; }
    previa.style.backgroundImage = `url('${URL.createObjectURL(f)}')`; previa.classList.add('tem');
    $('#foto-nome').textContent = 'Foto escolhida. Toque para trocar';
  });

  if ($('#btn-mic')) $('#btn-mic').addEventListener('click', () => {
    if (!SR) { preenche('tapioca de frango com catupiry, doze reais'); toast('Este navegador não tem voz. Mostrando um exemplo.'); return; }
    if (ouvindo) { rec.stop(); return; }
    rec = new SR(); rec.lang = 'pt-BR'; rec.interimResults = true;
    rec.onstart = () => { ouvindo = true; $('#btn-mic').classList.add('ouvindo'); $('#mic-rotulo').textContent = 'Ouvindo… pode falar'; };
    rec.onresult = (e) => {
      const r = e.results[e.results.length - 1], t = r[0].transcript;
      if (r.isFinal) preenche(t); else { $('#ouvido').textContent = t + '…'; $('#ouvido').classList.add('tem'); }
    };
    rec.onerror = (e) => toast(e.error === 'not-allowed' ? 'Permita o uso do microfone para falar' : 'Não consegui ouvir. Tente de novo');
    rec.onend = () => { ouvindo = false; $('#btn-mic').classList.remove('ouvindo'); $('#mic-rotulo').textContent = 'Toque para falar'; };
    rec.start();
  });
  // se a pessoa editar o nome à mão depois, continua marcado como voz (o cadastro começou falando)

  // ---- aviso do Pix ----
  const modal = $('#modal-pix'), ok = $('#id_v-conferiu_no_banco'), confirma = $('#pix-confirma');
  $('#btn-vendi').addEventListener('click', () => { ok.checked = false; confirma.disabled = true; modal.classList.add('on'); });
  ok.addEventListener('change', () => { confirma.disabled = !ok.checked; });
  $('#pix-fecha').addEventListener('click', () => { modal.classList.remove('on'); toast('Aguarde o dinheiro entrar antes de entregar'); });
  modal.addEventListener('click', (e) => { if (e.target === modal) modal.classList.remove('on'); });

  window.vitrineInterpreta = interpreta; // para teste no console
})();
