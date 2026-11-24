// Painel do comerciante: cadastro por voz (Web Speech API) e aviso do Pix.
(function () {
  const $ = (s) => document.querySelector(s);
  const campoNome = $('#id_p-nome'), campoPreco = $('#id_p-preco'), campoVoz = $('#id_p-cadastrado_por_voz');
  const campoTam = $('#id_p-tamanho'), campoDesc = $('#id_p-descricao');

  function toast(msg) {
    const t = $('#toast'); t.textContent = msg; t.classList.add('on');
    clearTimeout(t._t); t._t = setTimeout(() => t.classList.remove('on'), 2600);
  }

  // ---- números falados -> algarismos ----
  const NUM = { zero: 0, um: 1, uma: 1, dois: 2, duas: 2, 'três': 3, tres: 3, quatro: 4, cinco: 5, seis: 6, sete: 7, oito: 8, nove: 9, dez: 10,
    onze: 11, doze: 12, treze: 13, quatorze: 14, catorze: 14, quinze: 15, dezesseis: 16, dezessete: 17, dezoito: 18, dezenove: 19,
    vinte: 20, trinta: 30, quarenta: 40, cinquenta: 50, sessenta: 60, setenta: 70, oitenta: 80, noventa: 90, cem: 100, cento: 100,
    duzentos: 200, duzentas: 200, trezentos: 300, trezentas: 300, quatrocentos: 400, quatrocentas: 400, quinhentos: 500, quinhentas: 500,
    seiscentos: 600, setecentos: 700, oitocentos: 800, novecentos: 900, mil: 1000 };
  // palavras que vêm depois de um número de preço ou de tamanho
  const UNID = /^(reais|real|conto|contos|centavos?|gramas?|g|quilos?|kg|quilogramas?|ml|mililitros?|litros?|unidades?|d[uú]zias?|cm|cent[ií]metros?|metros?)$/;
  // "um"/"uma" só vira número antes de uma unidade ("um quilo", "uma dúzia"); senão é artigo ("uma tapioca")
  function numerosPorExtenso(f) {
    const w = f.split(/\s+/), out = [];
    for (let i = 0; i < w.length; i++) {
      if (NUM[w[i]] == null || ((w[i] === 'um' || w[i] === 'uma') && !UNID.test(w[i + 1] || ''))) { out.push(w[i]); continue; }
      let total = 0, j = i;
      while (j < w.length && (NUM[w[j]] != null || (w[j] === 'e' && NUM[w[j + 1]] != null && w[j + 1] !== 'um' && w[j + 1] !== 'uma'))) {
        if (w[j] === 'mil') total = (total || 1) * 1000; else if (w[j] !== 'e') total += NUM[w[j]];
        j++;
      }
      out.push(String(total)); i = j - 1;
    }
    return out.join(' ');
  }

  const N = '(\\d+(?:[.,]\\d+)?)';
  // tamanho: só quando vem com uma unidade conhecida (sem unidade, não chuta)
  const num = (s) => parseFloat(String(s).replace(',', '.'));
  const virgula = (v) => String(+v.toFixed(3)).replace('.', ',');
  const TAMANHOS = [
    // compostos: "1 kg e 600 g" -> 1,6 kg; "um quilo e meio" -> 1,5 kg; "1 litro e 500 ml" -> 1,5 L
    [new RegExp(N + '\\s*(?:quilos?|kg|quilogramas?)\\s+e\\s+' + N + '\\s*(?:gramas?|g)\\b'), (m) => `${virgula(num(m[1]) + num(m[2]) / 1000)} kg`],
    [new RegExp(N + '\\s*(?:quilos?|kg|quilogramas?)\\s+e\\s+meio\\b'), (m) => `${virgula(num(m[1]) + 0.5)} kg`],
    [new RegExp(N + '\\s*(?:litros?|l)\\s+e\\s+' + N + '\\s*(?:ml|mililitros?)\\b'), (m) => `${virgula(num(m[1]) + num(m[2]) / 1000)} L`],
    [new RegExp(N + '\\s*litros?\\s+e\\s+meio\\b'), (m) => `${virgula(num(m[1]) + 0.5)} L`],
    [/\bmeio\s+(quilo|kg)\b/, () => '500 g'],
    [/\bmeio\s+litro\b/, () => '500 ml'],
    [/\bmeia\s+d[uú]zia\b/, () => 'meia dúzia'],
    [new RegExp(N + '\\s*(gramas?|g)\\b'), (m) => `${m[1]} g`],
    [new RegExp(N + '\\s*(quilos?|kg|quilogramas?)\\b'), (m) => `${m[1]} kg`],
    [new RegExp(N + '\\s*(ml|mililitros?)\\b'), (m) => `${m[1]} ml`],
    [new RegExp(N + '\\s*litros?\\b'), (m) => `${m[1]} L`],
    [new RegExp(N + '\\s*d[uú]zias?\\b'), (m) => (m[1] === '1' ? '1 dúzia' : `${m[1]} dúzias`)],
    [new RegExp(N + '\\s*(cm|cent[ií]metros?)\\b'), (m) => `${m[1]} cm`],
    [new RegExp(N + '\\s*metros?\\b'), (m) => `${m[1]} m`],
    [/\btamanho\s+(pp|p|m|g|gg|xg|[uú]nico)\b/, (m) => `Tamanho ${m[1].toUpperCase().replace('ÚNICO', 'único').replace('UNICO', 'único')}`],
    [/\b(?:n[uú]mero|n[º°o])\s*(\d{2})\b/, (m) => `Nº ${m[1]}`],
    [/\b(?:a|por)\s+unidade\b|\bunidade\b/, () => 'unidade'],
  ];

  // Entende a frase em qualquer ordem: "bolo de macaxeira, 500 gramas, quinze reais"
  // | "quinze reais o bolo de macaxeira de meio quilo" | "cocada 4,50"
  function interpreta(frase) {
    // o Chrome costuma escrever "quinze reais" como "R$ 15" ou "R$ 15,50": vira "15,50 reais"
    // e o Edge escreve "80 BRL" ou "BRL 80" (o código da moeda)
    const t = frase.toLowerCase()
      .replace(/r\$\s*(\d+(?:[.,]\d+)?)/g, ' $1 reais ').replace(/\bbrl\s*(\d+(?:[.,]\d+)?)/g, ' $1 reais ')
      .replace(/(\d+(?:[.,]\d+)?)\s*brl\b/g, ' $1 reais ').replace(/r\$|\bbrl\b/g, ' ');
    let f = ' ' + numerosPorExtenso(t.replace(/[!?;]/g, ' ').replace(/\s+/g, ' ').trim()) + ' ';
    let preco = null, tamanho = '';
    // preço: o número que vem com "reais" (e, se tiver, os centavos)
    const p = f.match(new RegExp('(?:\\s(?:por|custa|a)\\s+)?' + N + '\\s*(?:reais|real|contos?)(?:\\s+e\\s+(\\d+)(?:\\s*centavos?)?)?'));
    if (p) {
      preco = parseFloat(p[1].replace(',', '.')) + (p[2] ? parseInt(p[2], 10) / 100 : 0);
      f = f.replace(p[0], ' , ');
    }
    for (const [re, fmt] of TAMANHOS) {
      const m = f.match(re);
      if (m) { tamanho = fmt(m); f = f.replace(m[0], ' , '); break; }
    }
    // sem "reais": um número solto no fim é o preço ("cocada 4,50")
    if (preco == null) {
      const n = f.match(/[,\s](\d+(?:[.,]\d{1,2})?)[\s,]*$/);
      if (n) { preco = parseFloat(n[1].replace(',', '.')); f = f.slice(0, n.index) + ' '; }
    }
    // o que sobra é o nome do produto (sem conectivos soltos nas pontas)
    const nome = f.replace(/\s*,\s*/g, ' , ').replace(/\bde\s+(,\s*)*de\b/g, 'de').split(',').map((s) => s.trim()).filter(Boolean).join(' ')
      .replace(/^(o|a|os|as|um|uma|é|e|por|custa|de|do|da|com)\s+/, '').replace(/\s+(o|a|é|e|por|custa|de|do|da|com|cada)$/, '')
      .replace(/\s+/g, ' ').trim();
    return { nome, tamanho, preco };
  }

  const reaisTxt = (v) => v.toFixed(2).replace('.', ',');
  function preenche(frase) {
    const o = $('#ouvido'); o.textContent = '“' + frase + '”'; o.classList.add('tem');
    const r = interpreta(frase);
    if (r.nome) campoNome.value = r.nome.charAt(0).toUpperCase() + r.nome.slice(1);
    if (r.preco != null) campoPreco.value = reaisTxt(r.preco);
    if (r.tamanho && campoTam) campoTam.value = r.tamanho;
    campoVoz.value = 'True';
    toast(r.preco != null ? 'Entendi! Confira e coloque na vitrine' : 'Entendi o produto. Falta o preço');
    // repete em voz alta o que entendeu, para quem tem dificuldade de leitura
    if (window.vitrineFala) {
      const tam = r.tamanho ? `, ${r.tamanho.replace(/(\d) g$/, '$1 gramas').replace(/(\d) kg$/, '$1 quilo').replace(/(\d) ml$/, '$1 mililitros').replace(/(\d) L$/, '$1 litro')}` : '';
      const preco = r.preco != null ? `, ${reaisTxt(r.preco)} reais` : '. Faltou o preço, fale de novo';
      window.vitrineFala(`Entendi: ${r.nome}${tam}${preco}. Se estiver certo, toque em colocar na vitrine.`);
    }
  }

  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  let rec = null, botaoAtivo = null;
  // abre o microfone; cada botão diz o que fazer com o que ouviu
  function ouvir(botao, rotulo, aoTerminar, aoOuvirParcial) {
    if (rec) { const mesmo = botaoAtivo === botao; rec.stop(); if (mesmo) return; }
    rec = new SR(); rec.lang = 'pt-BR'; rec.interimResults = true; botaoAtivo = botao;
    const txtRotulo = rotulo ? rotulo.textContent : '';
    rec.onstart = () => { botao.classList.add('ouvindo'); botao.setAttribute('aria-pressed', 'true'); if (rotulo) rotulo.textContent = 'Ouvindo… pode falar'; };
    rec.onresult = (e) => {
      const r = e.results[e.results.length - 1], t = r[0].transcript;
      if (r.isFinal) aoTerminar(t); else if (aoOuvirParcial) aoOuvirParcial(t);
    };
    rec.onerror = (e) => toast(e.error === 'not-allowed' ? 'Permita o uso do microfone para falar' : 'Não consegui ouvir. Tente de novo');
    rec.onend = () => { botao.classList.remove('ouvindo'); botao.setAttribute('aria-pressed', 'false'); if (rotulo) rotulo.textContent = txtRotulo; rec = null; botaoAtivo = null; };
    rec.start();
  }

  // foto do produto: mostra a prévia antes de enviar
  const campoFoto = $('#id_p-imagem');
  if (campoFoto) campoFoto.addEventListener('change', () => {
    const f = campoFoto.files[0], previa = $('#foto-previa');
    if (!f) return;
    if (f.size > 5 * 1024 * 1024) { toast('Foto grande demais. Use uma de até 5 MB'); campoFoto.value = ''; return; }
    previa.style.backgroundImage = `url('${URL.createObjectURL(f)}')`; previa.classList.add('tem');
    $('#foto-nome').textContent = 'Foto escolhida. Toque para trocar';
  });

  // microfone grande: produto, tamanho e preço numa frase só, em qualquer ordem
  if ($('#btn-mic')) $('#btn-mic').addEventListener('click', () => {
    if (!SR) { preenche('tapioca de frango com catupiry, doze reais'); toast('Este navegador não tem voz. Mostrando um exemplo.'); return; }
    ouvir($('#btn-mic'), $('#mic-rotulo'), preenche, (t) => { $('#ouvido').textContent = t + '…'; $('#ouvido').classList.add('tem'); });
  });

  // microfone da descrição: o que a pessoa fala vai inteiro para o campo
  const btnDesc = $('#btn-mic-desc');
  if (btnDesc && campoDesc) btnDesc.addEventListener('click', () => {
    if (!SR) { toast('Este navegador não tem voz. Escreva a descrição.'); return; }
    const antes = campoDesc.value.trim(), max = parseInt(campoDesc.getAttribute('maxlength') || '200', 10);
    const junta = (t) => {
      let s = t.trim(); s = s.charAt(0).toUpperCase() + s.slice(1);
      return (antes ? antes + (/[.!?]$/.test(antes) ? ' ' : '. ') + s : s).slice(0, max);
    };
    ouvir(btnDesc, null, (t) => {
      campoDesc.value = junta(t); campoVoz.value = 'True';
      toast('Descrição preenchida. Confira o texto');
      if (window.vitrineFala) window.vitrineFala(`Escrevi: ${campoDesc.value}`);
    }, (t) => { campoDesc.value = junta(t); });
  });

  window.vitrineInterpreta = interpreta; // para teste no console
})();
