from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models


class Banca(models.Model):
    """A vitrine de um comerciante: a loja, banca ou barraca do bairro."""

    class Categoria(models.TextChoices):
        COMIDA = 'comida', 'Comida e doces'
        FRUTAS = 'frutas', 'Frutas e coco'
        ARTESANATO = 'artesanato', 'Artesanato'
        ROUPAS = 'roupas', 'Roupas e brechó'
        SERVICOS = 'servicos', 'Serviços'

    # nomes de ícones do pacote Lucide (lucide.dev)
    ICONES = {'comida': 'utensils', 'frutas': 'citrus', 'artesanato': 'palette', 'roupas': 'shirt', 'servicos': 'scissors'}

    dono = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='banca')
    nome = models.CharField('nome da loja', max_length=80)
    responsavel = models.CharField('quem vende', max_length=80, help_text='Como os clientes conhecem você. Ex.: Aparecida (Dona Cida)')
    categoria = models.CharField(max_length=20, choices=Categoria.choices)
    historia = models.TextField('nossa história', blank=True)
    bairro = models.CharField(max_length=60)
    ponto = models.CharField('ponto de referência', max_length=100)
    cep = models.CharField('CEP', max_length=9, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    whatsapp = models.CharField(
        max_length=13,
        validators=[RegexValidator(r'^55\d{10,11}$', 'Use 55 + DDD + número, só dígitos.')],
        help_text='Ex.: 5582999998888',
    )
    # dias da semana em que a loja abre, guardados como 'seg,ter,qua' (o comerciante marca cada um)
    DIAS_SEMANA = [('seg', 'Segunda'), ('ter', 'Terça'), ('qua', 'Quarta'), ('qui', 'Quinta'),
                   ('sex', 'Sexta'), ('sab', 'Sábado'), ('dom', 'Domingo')]

    class Dias:  # combinações comuns, usadas nas lojas de demonstração
        TODOS = 'seg,ter,qua,qui,sex,sab,dom'
        SEG_SEX = 'seg,ter,qua,qui,sex'
        SEG_SAB = 'seg,ter,qua,qui,sex,sab'
        FDS = 'sab,dom'

    dias = models.CharField('dias que abre', max_length=30, blank=True)
    # dias com horário diferente do normal, ex.: {'sab': ['07:00', '12:00']}
    horarios_dia = models.JSONField('horário diferente em alguns dias', default=dict, blank=True)
    abre = models.TimeField('abre às', null=True, blank=True)
    fecha = models.TimeField('fecha às', null=True, blank=True)
    aberta = models.BooleanField('aberta agora', default=True)
    da_comunidade = models.BooleanField('selo da comunidade', default=True)
    emoji = models.CharField(max_length=8, default='🛍️')
    cor = models.CharField(max_length=7, default='#ccfbf1')
    foto = models.CharField('foto de capa (arquivo estático)', max_length=120, blank=True,
                            help_text='Ex.: vitrine/fotos/capa-cida.jpg')
    capa = models.FileField('foto de capa enviada', upload_to='lojas/', blank=True)
    visivel = models.BooleanField('aparece no site', default=True,
                                  help_text='Desmarque para esconder uma loja falsa ou com problema. O cadastro não precisa de aprovação.')
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'loja'
        verbose_name_plural = 'lojas'

    def __str__(self):
        return self.nome

    @property
    def primeiro_nome(self):
        return self.responsavel.split(',')[0].split('(')[0].strip().split(' ')[0]

    @property
    def responsavel_nome(self):
        return self.responsavel.split(',')[0].strip()

    @classmethod
    def texto_dos_dias(cls, codigos_marcados):
        """['ter','qua','qui','sex','sab'] -> 'Terça a sábado'; ['seg','qua','sex'] -> 'Segunda, quarta e sexta'."""
        codigos = [c for c, _ in cls.DIAS_SEMANA]
        nomes = [n for _, n in cls.DIAS_SEMANA]
        marcados = [i for i, c in enumerate(codigos) if c in codigos_marcados]
        if not marcados:
            return ''
        if len(marcados) == 7:
            return 'Todos os dias'
        seguidos = marcados == list(range(marcados[0], marcados[-1] + 1))
        if seguidos and len(marcados) >= 3:
            return f'{nomes[marcados[0]]} a {nomes[marcados[-1]].lower()}'
        lista = [nomes[i] if k == 0 else nomes[i].lower() for k, i in enumerate(marcados)]
        return lista[0] if len(lista) == 1 else ', '.join(lista[:-1]) + ' e ' + lista[-1]

    @property
    def dias_texto(self):
        return self.texto_dos_dias((self.dias or '').split(','))

    @property
    def horario_texto(self):
        """Ex.: 'Terça a sexta, das 7h às 18h; sábado, das 7h às 12h'. Vazio se o comerciante não informou."""
        def hora(h):
            hh, mm = (h.hour, h.minute) if hasattr(h, 'hour') else map(int, h.split(':'))
            return f'{hh}h' + (f'{mm:02d}' if mm else '')

        def faixa(a, f):
            return f'das {hora(a)} às {hora(f)}' if a and f else ''

        marcados = [c for c, _ in self.DIAS_SEMANA if c in (self.dias or '').split(',')]
        especiais = {d: h for d, h in (self.horarios_dia or {}).items() if d in marcados and h and len(h) == 2}
        # agrupa os dias pelo horário: primeiro o horário normal, depois os diferentes
        grupos = {}
        normais = [d for d in marcados if d not in especiais]
        if normais or not marcados:
            grupos[faixa(self.abre, self.fecha)] = normais
        for d in marcados:
            if d in especiais:
                grupos.setdefault(faixa(*especiais[d]), []).append(d)
        partes = []
        for k, (hor, dias) in enumerate(grupos.items()):
            txt = ', '.join(p for p in (self.texto_dos_dias(dias), hor) if p)
            if txt:
                partes.append(txt if not partes else txt[0].lower() + txt[1:])
        return '; '.join(partes)

    @property
    def icone_categoria(self):
        return self.ICONES.get(self.categoria, 'store')

    @property
    def foto_url(self):
        """Capa enviada pelo comerciante; senão, a foto da demonstração; senão, vazio."""
        if self.capa:
            return self.capa.url
        if self.foto:
            from django.templatetags.static import static
            return static(self.foto)
        return ''


class Produto(models.Model):
    class Disponibilidade(models.TextChoices):
        PRONTA = 'pronta', 'Pronta entrega'
        ENCOMENDA = 'encomenda', 'Sob encomenda'

    banca = models.ForeignKey(Banca, on_delete=models.CASCADE, verbose_name='loja', related_name='produtos')
    nome = models.CharField(max_length=100)
    tamanho = models.CharField('tamanho / unidade', max_length=40, default='unidade')
    descricao = models.CharField('descrição', max_length=200, blank=True, help_text='Opcional. Ex.: feita com goma fresca e queijo coalho.')
    preco = models.DecimalField('preço', max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)])
    disponibilidade = models.CharField(max_length=10, choices=Disponibilidade.choices, default=Disponibilidade.PRONTA)
    emoji = models.CharField(max_length=8, default='📦')
    foto = models.CharField('foto (arquivo estático)', max_length=120, blank=True)
    imagem = models.FileField('foto enviada', upload_to='produtos/', blank=True)
    cadastrado_por_voz = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.nome} ({self.banca})'

    @property
    def foto_url(self):
        """Foto enviada pelo comerciante; senão, a foto da demonstração; senão, vazio."""
        if self.imagem:
            return self.imagem.url
        if self.foto:
            from django.templatetags.static import static
            return static(self.foto)
        return ''


class Venda(models.Model):
    """Registro de venda confirmada pelo comerciante depois de conferir o Pix no banco."""

    banca = models.ForeignKey(Banca, on_delete=models.CASCADE, verbose_name='loja', related_name='vendas')
    conferiu_no_banco = models.BooleanField(default=False)
    registrada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-registrada_em']

    def __str__(self):
        return f'Venda de {self.banca} em {self.registrada_em:%d/%m %H:%M}'


class Avaliacao(models.Model):
    """Nota de 1 a 5 e comentário deixados por um cliente sobre uma banca."""

    banca = models.ForeignKey(Banca, on_delete=models.CASCADE, verbose_name='loja', related_name='avaliacoes')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True,
                              related_name='avaliacoes', help_text='Vazio só nas avaliações de demonstração.')
    nome = models.CharField('seu nome', max_length=40)
    nota = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.TextField('comentário', max_length=500)
    visivel = models.BooleanField(default=True, help_text='Desmarque para esconder um comentário ofensivo.')
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criada_em']
        constraints = [models.UniqueConstraint(fields=['banca', 'autor'], name='uma_avaliacao_por_pessoa_por_banca')]
        verbose_name = 'avaliação'
        verbose_name_plural = 'avaliações'

    def __str__(self):
        return f'{self.nota}★ {self.banca} – {self.nome}'
