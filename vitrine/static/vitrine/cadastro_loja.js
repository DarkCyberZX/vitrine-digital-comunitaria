// Cadastro da loja: marcar o local no mapa, usar o GPS e mostrar a prévia da foto.
(function () {
  const $ = (s) => document.querySelector(s);
  const lat = $('#id_l-latitude'), lng = $('#id_l-longitude'), aviso = $('#cl-mapa-ok');
  const fala = (t) => { aviso.textContent = t; };

  // mostrar a senha
  document.querySelectorAll('.ver-senha').forEach((c) => c.addEventListener('change', () => {
    document.querySelectorAll('input[type=password], input[data-senha]').forEach((i) => { i.dataset.senha = '1'; i.type = c.checked ? 'text' : 'password'; });
  }));

  if (!lat) return; // etapa 1 (só a conta): não tem mapa nem foto

  // prévia da foto da loja
  const foto = $('#id_l-capa');
  if (foto) foto.addEventListener('change', () => {
    const f = foto.files[0]; if (!f) return;
    if (f.size > 5 * 1024 * 1024) { fala('Foto grande demais. Use uma de até 5 MB.'); foto.value = ''; return; }
    const p = $('#cl-previa'); p.style.backgroundImage = `url('${URL.createObjectURL(f)}')`; p.classList.add('tem');
    $('#cl-foto-nome').textContent = 'Foto escolhida. Toque para trocar';
  });

  if (!window.L) { fala('O mapa não carregou. Verifique a internet e recarregue a página.'); return; }
  const inicial = lat.value && lng.value ? [parseFloat(lat.value.replace(',', '.')), parseFloat(lng.value.replace(',', '.'))] : null;
  const mapa = L.map('cl-mapa', { scrollWheelZoom: false }).setView(inicial || [-9.6498, -35.7089], inicial ? 17 : 13);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap' }).addTo(mapa);
  const pino = L.divIcon({ className: 'cl-pino', html: '<span></span>', iconSize: [34, 44], iconAnchor: [17, 42] });
  let marcador = null;

  function marca(p, msg) {
    const v = [Number(p.lat.toFixed(6)), Number(p.lng.toFixed(6))];
    lat.value = v[0]; lng.value = v[1];
    if (!marcador) {
      marcador = L.marker(v, { icon: pino, draggable: true, keyboard: true, title: 'Local da loja (arraste para ajustar)' }).addTo(mapa);
      marcador.on('dragend', () => marca(marcador.getLatLng(), 'Local ajustado.'));
    } else marcador.setLatLng(v);
    $('#cl-mapa').classList.add('marcado');
    fala(msg || 'Local marcado. Se precisar, arraste o marcador.');
  }
  if (inicial) marca({ lat: inicial[0], lng: inicial[1] }, 'Local marcado.');
  mapa.on('click', (e) => marca(e.latlng));

  // ---------- CEP: preenche bairro e rua (ViaCEP) e leva o mapa até a rua (OpenStreetMap) ----------
  const cep = $('#id_l-cep'), bairro = $('#id_l-bairro'), ponto = $('#id_l-ponto'), cepMsg = $('#cl-cep-msg');
  let ultimoCep = '';
  const cepAviso = (t, tipo) => { cepMsg.textContent = t; cepMsg.className = 'cl-cep-msg ' + (tipo || ''); };
  cep.addEventListener('input', () => {
    const d = cep.value.replace(/\D/g, '').slice(0, 8);
    cep.value = d.length > 5 ? d.slice(0, 5) + '-' + d.slice(5) : d; // máscara 57000-000
    if (d.length === 8 && d !== ultimoCep) buscaCep(d);
    if (d.length < 8) cepAviso('');
  });
  async function buscaCep(d) {
    ultimoCep = d; cepAviso('Procurando o CEP…');
    try {
      const r = await fetch(`https://viacep.com.br/ws/${d}/json/`);
      const e = await r.json();
      if (e.erro) { cepAviso('CEP não encontrado. Confira os números ou preencha o bairro à mão.', 'ruim'); return; }
      if (e.localidade !== 'Maceió') cepAviso(`Esse CEP é de ${e.localidade}. A Vitrine, por enquanto, é só de Maceió.`, 'ruim');
      else cepAviso(`Achamos: ${[e.logradouro, e.bairro].filter(Boolean).join(', ')}.`, 'bom');
      if (e.bairro) bairro.value = e.bairro;
      if (e.logradouro && !ponto.value.trim()) ponto.value = e.logradouro;
      if (e.localidade === 'Maceió') vaiParaRua(e, d);
    } catch (err) {
      cepAviso('Não deu para consultar o CEP agora. Preencha o bairro à mão.', 'ruim');
    }
  }
  async function vaiParaRua(e, d) {
    const q = new URLSearchParams({ format: 'json', limit: '1', city: 'Maceió', state: 'Alagoas', country: 'Brasil' });
    if (e.logradouro) q.set('street', e.logradouro); else q.set('postalcode', d);
    try {
      const r = await fetch('https://nominatim.openstreetmap.org/search?' + q, { headers: { 'Accept-Language': 'pt-BR' } });
      const [achou] = await r.json();
      if (!achou) { fala('Não achamos a rua no mapa. Toque no mapa no lugar da loja.'); return; }
      const p = { lat: parseFloat(achou.lat), lng: parseFloat(achou.lon) };
      mapa.setView([p.lat, p.lng], 17);
      marca(p, 'Levamos o mapa até a sua rua. Arraste o marcador até a porta da loja.');
    } catch (err) { fala('Toque no mapa no lugar da loja.'); }
  }

  $('#cl-gps').addEventListener('click', () => {
    if (!navigator.geolocation) { fala('Este aparelho não informa a localização. Toque no mapa para marcar.'); return; }
    fala('Procurando onde você está…');
    navigator.geolocation.getCurrentPosition(
      (pos) => { const p = { lat: pos.coords.latitude, lng: pos.coords.longitude }; mapa.setView([p.lat, p.lng], 17); marca(p, 'Pronto! Marcamos onde você está. Confira e arraste se precisar.'); },
      () => fala('Não deu para pegar a localização. Toque no mapa no lugar da loja.'),
      { enableHighAccuracy: true, timeout: 10000 });
  });
})();
