import random
from urllib.parse import quote

from django.contrib import messages
from django.contrib.auth import login
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.db.models import Avg, Count, Min, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import AvaliacaoForm, CadastroForm, HistoriaForm, LojaForm, ProdutoForm, VendaForm
from .models import Avaliacao, Banca, Produto, Venda



def inicio(request):
    visiveis = Q(avaliacoes__visivel=True)
    bancas = (Banca.objects.filter(visivel=True).annotate(qtd=Count('produtos', distinct=True), menor=Min('produtos__preco'),
                                     media=Avg('avaliacoes__nota', filter=visiveis),
                                     n_aval=Count('avaliacoes', filter=visiveis, distinct=True))
              .prefetch_related('produtos', 'avaliacoes'))
    dados = [{
        'id': b.id, 'nome': b.nome, 'resp': b.responsavel, 'cat': b.categoria, 'icone': b.icone_categoria, 'emoji': b.emoji,
        'cor': b.cor, 'bairro': b.bairro, 'ponto': b.ponto, 'cep': b.cep,
        'lat': float(b.latitude), 'lng': float(b.longitude), 'aberta': b.aberta, 'local': b.da_comunidade,
        'qtd': b.qtd, 'menor': float(b.menor) if b.menor is not None else None,
        'busca': ' '.join(p.nome for p in b.produtos.all()),
        'produtos': [p.nome for p in b.produtos.all()], 'pdesc': [p.descricao for p in b.produtos.all()],
        'cat_nome': b.get_categoria_display(),
        'url': reverse('banca', args=[b.id]),
        'foto': b.foto_url,
        'media': round(b.media, 1) if b.media else None, 'n_aval': b.n_aval,
        'trecho': _ultimo_comentario(b),
        'pronta': any(p.disponibilidade == 'pronta' for p in b.produtos.all()),
    } for b in bancas]
    bairros = sorted({d['bairro'] for d in dados})
    categorias = [(v, n, Banca.ICONES[v], sum(1 for d in dados if d['cat'] == v)) for v, n in Banca.Categoria.choices]
    # "Histórias de quem faz": as 3 lojas mais bem avaliadas que têm história e foto
    # "Histórias de quem faz": sorteio a cada visita, para toda loja ter a mesma chance;
    # primeiro uma loja de cada categoria, e só repete categoria se faltar loja
    candidatas = [b for b in bancas if b.historia and b.foto_url]
    random.shuffle(candidatas)
    com_historia, vistas = [], set()
    for b in candidatas:
        if b.categoria not in vistas and len(com_historia) < 3:
            com_historia.append(b); vistas.add(b.categoria)
    com_historia += [b for b in candidatas if b not in com_historia][:3 - len(com_historia)]
    historias = [{'b': b, 'trecho': _trecho(b.historia, 150)} for b in com_historia]
    # "O que os vizinhos dizem": avaliações visíveis mais recentes, no máximo 2 por loja
    recentes, por_loja = [], {}
    for a in Avaliacao.objects.filter(visivel=True, banca__visivel=True).select_related('banca').order_by('-criada_em', '-id'):
        if por_loja.get(a.banca_id, 0) < 2:
            recentes.append(a); por_loja[a.banca_id] = por_loja.get(a.banca_id, 0) + 1
        if len(recentes) == 6:
            break
    return render(request, 'vitrine/inicio.html', {
        'bancas_json': dados, 'categorias': categorias, 'aba': 'inicio',
        'bairros': bairros, 'total_bancas': len(dados), 'total_produtos': Produto.objects.filter(banca__visivel=True).count(),
        'historias': historias, 'depoimentos': recentes,
        'nota_geral': Avaliacao.objects.filter(visivel=True, banca__visivel=True).aggregate(m=Avg('nota'))['m'],
    })


def _trecho(texto, limite):
    texto = ' '.join(texto.split())
    return texto if len(texto) <= limite else texto[:limite - 1].rsplit(' ', 1)[0] + '…'


def _ultimo_comentario(b):
    for a in b.avaliacoes.all():  # já vem do mais novo para o mais antigo
        if a.visivel:
            return a.comentario if len(a.comentario) <= 90 else a.comentario[:87].rsplit(' ', 1)[0] + '…'
    return ''


def _classes_estrelas(media):
    if media is None:
        return []
    return ['cheia' if media >= i - 0.25 else 'meia' if media >= i - 0.75 else '' for i in range(1, 6)]


def banca(request, pk):
    b = get_object_or_404(Banca.objects.prefetch_related('produtos'), pk=pk)
    if not b.visivel and b.dono_id != request.user.id:  # loja escondida pelo administrador
        raise Http404
    eh_dono = request.user.is_authenticated and b.dono_id == request.user.id
    minha = b.avaliacoes.filter(autor=request.user).first() if request.user.is_authenticated else None
    form = AvaliacaoForm(instance=minha)
    if request.method == 'POST':
        destino = reverse('banca', args=[b.pk]) + '#avaliacoes'
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={quote(destino)}")
        if eh_dono:
            messages.error(request, 'Você não pode avaliar a sua própria banca.')
            return redirect(destino)
        form = AvaliacaoForm(request.POST, instance=minha)
        if form.is_valid():
            av = form.save(commit=False)
            av.banca, av.autor = b, request.user  # banca vem da URL e autor da sessão, nunca do formulário
            av.nome = (request.user.first_name or request.user.username)[:40]
            av.save()
            messages.success(request, 'Avaliação atualizada.' if minha else 'Obrigado! Sua avaliação foi publicada.')
            return redirect(destino)
        messages.error(request, 'Confira os campos da avaliação.')
    avaliacoes = list(b.avaliacoes.filter(visivel=True))
    total = len(avaliacoes)
    media = round(sum(a.nota for a in avaliacoes) / total, 1) if total else None
    barras = [(n, sum(1 for a in avaliacoes if a.nota == n)) for n in range(5, 0, -1)]
    barras = [(n, q, round(100 * q / total) if total else 0) for n, q in barras]
    msg = f'Olá! Vi sua loja "{b.nome}" na Vitrine Digital Comunitária e tenho interesse nos seus produtos.'
    link_zap = f'https://wa.me/{b.whatsapp}?text={quote(msg)}'
    return render(request, 'vitrine/banca.html', {
        'b': b, 'link_zap': link_zap, 'leitura': texto_para_ouvir(b), 'aba': 'inicio',
        'estrelas_media': _classes_estrelas(media),
        'minha': minha, 'eh_dono': eh_dono,
        'local_json': {'lat': float(b.latitude), 'lng': float(b.longitude), 'icone': b.icone_categoria},
        'avaliacoes': avaliacoes, 'media': media, 'total_aval': total, 'barras': barras, 'form_aval': form,
    })


def _reais_por_extenso(valor):
    reais, cent = int(valor), int(round((valor - int(valor)) * 100))
    txt = f'{reais} {"real" if reais == 1 else "reais"}'
    return txt + (f' e {cent} centavos' if cent else '')


def texto_para_ouvir(b):
    """Texto lido em voz alta pelo botão 'Ouvir' (para quem tem dificuldade de leitura ou baixa visão)."""
    partes = [f'{b.nome}. {"Aberta agora" if b.aberta else "Fechada agora"}. Fica em {b.ponto}, {b.bairro}.']
    notas = [a.nota for a in b.avaliacoes.all() if a.visivel]
    if notas:
        media = f'{sum(notas) / len(notas):.1f}'.replace('.', ',')
        partes.append(f'Nota {media} de 5, com {len(notas)} avaliações.')
    produtos = list(b.produtos.all())
    if produtos:
        partes.append(f'São {len(produtos)} produtos.')
        for p in produtos:
            entrega = 'pronta entrega' if p.disponibilidade == 'pronta' else 'sob encomenda'
            desc = f' {p.descricao.rstrip(".")}.' if p.descricao else ''
            partes.append(f'{p.nome}, {p.tamanho}: {_reais_por_extenso(p.preco)}, {entrega}.{desc}')
    partes.append('Para comprar, toque no botão verde Conversar no WhatsApp.')
    return ' '.join(partes)


def sobre(request):
    return render(request, 'vitrine/sobre.html', {'aba': 'sobre'})


def _banca_do_usuario(request):
    return getattr(request.user, 'banca', None) if request.user.is_authenticated else None


@login_required
def painel(request):
    minha = _banca_do_usuario(request)
    if minha is None:
        return redirect('cadastro_loja')  # quem ainda não tem loja vai direto cadastrar a sua

    # editar: o produto só é encontrado se for da loja de quem está logado (senão 404)
    editar_id = request.POST.get('editar') or request.GET.get('editar')
    editando = get_object_or_404(Produto, pk=editar_id, banca=minha) if editar_id else None

    form = ProdutoForm(prefix='p', instance=editando)
    hist_form = HistoriaForm(instance=minha, prefix='h')
    venda_form = VendaForm(prefix='v')

    if request.method == 'POST':
        acao = request.POST.get('acao')
        if acao == 'produto':
            form = ProdutoForm(request.POST, request.FILES, prefix='p', instance=editando)
            if form.is_valid():
                if editando and request.POST.get('tirar_foto') and not request.FILES.get('p-imagem'):
                    form.instance.imagem = ''
                    form.instance.foto = ''
                p = form.save(commit=False)
                p.banca = minha  # o dono vem da sessão, nunca do formulário
                if not editando:
                    p.emoji = '🆕'
                p.save()
                messages.success(request, 'Produto atualizado.' if editando else 'Pronto! Já está na sua vitrine.')
                return redirect('painel')
        elif acao == 'historia':
            hist_form = HistoriaForm(request.POST, instance=minha, prefix='h')
            if hist_form.is_valid():
                hist_form.save()
                messages.success(request, 'História salva.')
                return redirect('painel')
        elif acao == 'venda':
            venda_form = VendaForm(request.POST, prefix='v')
            if venda_form.is_valid():
                Venda.objects.create(banca=minha, conferiu_no_banco=True)
                messages.success(request, 'Venda registrada com segurança.')
                return redirect('painel')
            messages.error(request, 'Só confirme a entrega depois de ver o dinheiro no app do banco.')

    # resumo da loja para o comerciante acompanhar
    avaliacoes = minha.avaliacoes.filter(visivel=True)
    media = avaliacoes.aggregate(m=Avg('nota'))['m']
    return render(request, 'vitrine/painel.html', {
        'minha': minha, 'form': form, 'hist_form': hist_form, 'venda_form': venda_form, 'editando': editando,
        'produtos': minha.produtos.all(), 'vendas': minha.vendas.all()[:5], 'aba': 'vender',
        'media': media, 'estrelas_media': _classes_estrelas(media), 'total_aval': avaliacoes.count(),
        'recentes': avaliacoes[:3], 'total_vendas': minha.vendas.count(),
    })


@login_required
@require_POST
def remover_produto(request, pk):
    minha = _banca_do_usuario(request)
    # só encontra o produto se ele for da banca de quem está logado (senão 404)
    produto = get_object_or_404(Produto, pk=pk, banca=minha)
    produto.delete()
    messages.success(request, 'Produto retirado da vitrine.')
    return redirect('painel')


def cadastro(request):
    """Cadastro curto do cliente (nome, usuário e senha) para poder avaliar bancas."""
    proximo = request.POST.get('next') or request.GET.get('next') or ''
    if not url_has_allowed_host_and_scheme(proximo, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        proximo = ''
    if request.user.is_authenticated:
        return redirect(proximo or 'inicio')
    form = CadastroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f'Conta criada! Bem-vindo(a), {user.first_name}.')
        return redirect(proximo or 'inicio')
    return render(request, 'registration/cadastro.html', {'form': form, 'next': proximo})


def _cats():
    return [(v, n, Banca.ICONES[v]) for v, n in Banca.Categoria.choices]


def _bairros_conhecidos():
    return sorted(set(Banca.objects.filter(visivel=True).values_list('bairro', flat=True)))


def cadastro_loja(request):
    """O comerciante cria a própria loja, sem esperar aprovação. Sem conta, cria a conta junto."""
    if request.user.is_authenticated and _banca_do_usuario(request):
        return redirect('painel')
    sem_conta = not request.user.is_authenticated
    conta = CadastroForm(request.POST or None, prefix='c') if sem_conta else None
    loja = LojaForm(request.POST or None, request.FILES or None, prefix='l')
    if request.method == 'POST' and loja.is_valid() and (conta is None or conta.is_valid()):
        with transaction.atomic():  # ou cria conta e loja juntas, ou nenhuma
            user = conta.save() if conta else request.user
            nova = loja.save(commit=False)
            nova.dono = user  # o dono vem da sessão (ou da conta recém-criada), nunca do formulário
            nova.save()
        if conta:
            login(request, user)
        messages.success(request, 'Sua loja já está no ar! Agora coloque os seus produtos.')
        return redirect('painel')
    return render(request, 'vitrine/cadastro_loja.html', {
        'conta': conta, 'loja': loja, 'bairros': _bairros_conhecidos(), 'aba': 'vender', 'editando': False, 'categorias': _cats()})


@login_required
def editar_loja(request):
    """O comerciante muda os dados da própria loja (nome, endereço, mapa, WhatsApp, foto)."""
    minha = _banca_do_usuario(request)
    if minha is None:
        return redirect('cadastro_loja')
    loja = LojaForm(request.POST or None, request.FILES or None, prefix='l', instance=minha)
    if request.method == 'POST' and loja.is_valid():
        loja.save()
        messages.success(request, 'Dados da loja atualizados.')
        return redirect('painel')
    return render(request, 'vitrine/cadastro_loja.html', {
        'conta': None, 'loja': loja, 'bairros': _bairros_conhecidos(), 'aba': 'vender', 'editando': True, 'minha': minha, 'categorias': _cats()})
