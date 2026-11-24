from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, UserCreationForm
from django.contrib.auth.models import User
from django.db.models import Q

from .models import Avaliacao, Banca, Produto


class ProdutoForm(forms.ModelForm):
    # o JS aceita "8,50" e manda "8.50"; o campo também aceita vírgula digitada à mão
    preco = forms.CharField(label='Preço (R$)', widget=forms.TextInput(attrs={'inputmode': 'decimal', 'placeholder': '0,00'}))

    class Meta:
        model = Produto
        fields = ['nome', 'preco', 'tamanho', 'descricao', 'disponibilidade', 'imagem', 'cadastrado_por_voz']
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Nome do produto'}),
            'tamanho': forms.TextInput(attrs={'placeholder': 'Ex.: unidade, M, 500 g'}),
            'descricao': forms.Textarea(attrs={'rows': 2, 'maxlength': 200, 'placeholder': 'Ex.: feita com goma fresca e queijo coalho, servida quentinha'}),
            'cadastrado_por_voz': forms.HiddenInput(),
            'imagem': forms.FileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
        }

    # assinatura dos tipos aceitos: não confia só no nome do arquivo
    ASSINATURAS = {b'\xff\xd8\xff': 'jpg', b'\x89PNG\r\n\x1a\n': 'png'}

    def clean_imagem(self):
        return confere_foto(self.cleaned_data.get('imagem'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and not self.is_bound:  # ao editar, mostra 8,50 e não 8.50
            self.initial['preco'] = f'{self.instance.preco:.2f}'.replace('.', ',')

    def clean_preco(self):
        bruto = self.cleaned_data['preco'].replace('R$', '').replace(' ', '')
        if ',' in bruto:
            bruto = bruto.replace('.', '').replace(',', '.')
        try:
            from decimal import Decimal, InvalidOperation
            valor = Decimal(bruto)
        except Exception:
            raise forms.ValidationError('Digite o preço só com números. Ex.: 8,50')
        if valor <= 0:
            raise forms.ValidationError('O preço precisa ser maior que zero.')
        if valor >= Decimal('1000000'):
            raise forms.ValidationError('Preço alto demais.')
        return valor.quantize(Decimal('0.01'))


class HistoriaForm(forms.ModelForm):
    class Meta:
        model = Banca
        fields = ['historia', 'aberta']
        widgets = {'historia': forms.Textarea(attrs={'rows': 4})}


class VendaForm(forms.Form):
    conferiu_no_banco = forms.BooleanField(
        required=True, label='Conferi no app do banco e o dinheiro entrou',
        error_messages={'required': 'Só confirme depois de ver o dinheiro no app do banco.'},
    )


class AvaliacaoForm(forms.ModelForm):
    nota = forms.TypedChoiceField(
        label='Sua nota', coerce=int, choices=[(n, f'{n} estrela{"s" if n > 1 else ""}') for n in range(5, 0, -1)],
        widget=forms.RadioSelect, error_messages={'required': 'Escolha de 1 a 5 estrelas.'},
    )

    class Meta:
        model = Avaliacao
        fields = ['nota', 'comentario']
        widgets = {
            'comentario': forms.Textarea(attrs={'rows': 3, 'maxlength': 500, 'placeholder': 'Conte como foi a sua compra'}),
        }


class CadastroForm(UserCreationForm):
    """Cadastro curto: nome, usuário e senha (sem e-mail)."""
    first_name = forms.CharField(label='Seu nome', max_length=40,
                                 widget=forms.TextInput(attrs={'autocomplete': 'given-name', 'placeholder': 'Ex.: Maria'}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['first_name', 'username']
        labels = {'username': 'Usuário'}
        help_texts = {'username': 'É com ele que você entra. Só letras, números e @ . + - _ (sem espaço). Ex.: maria.silva'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'autocomplete': 'username', 'autocapitalize': 'none', 'placeholder': 'Ex.: maria.silva'})
        self.fields['password1'].label = 'Senha'
        self.fields['password1'].help_text = 'Pelo menos 8 letras ou números, e não pode ser só números.'
        self.fields['password2'].label = 'Repita a senha'
        self.fields['password2'].help_text = ''

    def clean_username(self):
        usuario = super().clean_username()
        # não deixa criar "Maria" se já existe "maria", nem usar o e-mail de uma conta antiga
        if User.objects.filter(Q(username__iexact=usuario) | Q(email__iexact=usuario)).exists():
            raise forms.ValidationError('Esse usuário já existe. Escolha outro.')
        return usuario


class EntrarForm(AuthenticationForm):
    """Entrar com o usuário (contas antigas criadas com e-mail também entram pelo e-mail)."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Usuário'
        self.fields['username'].widget.attrs.update({'autocomplete': 'username', 'autocapitalize': 'none', 'placeholder': 'Seu usuário'})


class EsqueciSenhaForm(PasswordResetForm):
    email = forms.EmailField(label='Seu e-mail', max_length=254,
                             widget=forms.EmailInput(attrs={'autocomplete': 'email', 'placeholder': 'O e-mail que você usou na conta'}))


class NovaSenhaForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].label = 'Senha nova'
        self.fields['new_password1'].help_text = 'Pelo menos 8 letras ou números, e não pode ser só números.'
        self.fields['new_password2'].label = 'Repita a senha nova'
        self.fields['new_password2'].help_text = ''


def confere_foto(arq):
    """Aceita só JPG, PNG ou WEBP de verdade (olha os primeiros bytes) e troca o nome do arquivo."""
    if not arq or not hasattr(arq, 'content_type'):  # sem foto nova: mantém a que já tinha
        return arq
    if arq.size > 5 * 1024 * 1024:
        raise forms.ValidationError('A foto é grande demais. Use uma de até 5 MB.')
    inicio = arq.read(12); arq.seek(0)
    tipo = next((t for assin, t in ProdutoForm.ASSINATURAS.items() if inicio.startswith(assin)), None)
    if tipo is None and inicio[:4] == b'RIFF' and inicio[8:12] == b'WEBP':
        tipo = 'webp'
    if tipo is None:
        raise forms.ValidationError('Envie uma foto em JPG, PNG ou WEBP.')
    import uuid
    arq.name = f'{uuid.uuid4().hex}.{tipo}'  # nome novo: nunca usa o nome enviado
    return arq


class LojaForm(forms.ModelForm):
    """Cadastro da loja feito pelo próprio comerciante, sem precisar de aprovação."""
    dias = forms.MultipleChoiceField(label='Dias que abre', required=False, choices=Banca.DIAS_SEMANA,
                                     widget=forms.CheckboxSelectMultiple)
    whatsapp = forms.CharField(label='WhatsApp da loja', max_length=20,
                               widget=forms.TextInput(attrs={'inputmode': 'tel', 'placeholder': '(82) 99999-8888', 'autocomplete': 'tel'}),
                               help_text='O número em que os clientes vão chamar você.')

    class Meta:
        model = Banca
        fields = ['nome', 'responsavel', 'categoria', 'whatsapp', 'dias', 'abre', 'fecha', 'bairro', 'ponto', 'cep', 'latitude', 'longitude', 'historia', 'capa']
        labels = {'nome': 'Nome da loja', 'responsavel': 'Como os clientes chamam você', 'categoria': 'O que você vende',
                  'ponto': 'Onde fica (rua ou ponto de referência)', 'cep': 'CEP (se souber)',
                  'historia': 'Sua história (se quiser)', 'capa': 'Foto da loja (se quiser)'}
        help_texts = {'responsavel': 'Ex.: Aparecida (Dona Cida)', 'historia': 'Conte quem você é e como faz seus produtos. Aparece na página da loja.'}
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Ex.: Tapiocaria da Cida'}),
            'responsavel': forms.TextInput(attrs={'placeholder': 'Ex.: Aparecida (Dona Cida)'}),
            'categoria': forms.RadioSelect,
            'bairro': forms.TextInput(attrs={'placeholder': 'Ex.: Ponta Verde', 'list': 'lista-bairros', 'autocomplete': 'off'}),
            'ponto': forms.TextInput(attrs={'placeholder': 'Ex.: Orla, em frente ao posto 7'}),
            'cep': forms.TextInput(attrs={'inputmode': 'numeric', 'placeholder': '57000-000'}),
            'latitude': forms.HiddenInput, 'longitude': forms.HiddenInput,
            'historia': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Ex.: Faço tapioca há 20 anos com a goma que eu mesma preparo.'}),
            'capa': forms.FileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
            'abre': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
            'fecha': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
        }
        error_messages = {'latitude': {'required': 'Marque no mapa onde fica a sua loja.'},
                          'longitude': {'required': 'Marque no mapa onde fica a sua loja.'}}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].choices = list(Banca.Categoria.choices)  # sem a opção vazia "-----"
        if not self.is_bound and self.instance.dias:
            self.initial['dias'] = self.instance.dias.split(',')
        if self.instance.pk and not self.is_bound and self.instance.whatsapp:
            n = self.instance.whatsapp[2:]  # mostra (82) 99999-8888 e não 5582999998888
            self.initial['whatsapp'] = f'({n[:2]}) {n[2:-4]}-{n[-4:]}'

    def clean_dias(self):
        ordem = [c for c, _ in Banca.DIAS_SEMANA]
        return ','.join(c for c in ordem if c in self.cleaned_data.get('dias', []))

    def clean_whatsapp(self):
        digitos = ''.join(c for c in self.cleaned_data['whatsapp'] if c.isdigit())
        if len(digitos) in (10, 11):
            digitos = '55' + digitos
        if not (digitos.startswith('55') and len(digitos) in (12, 13)):
            raise forms.ValidationError('Escreva o número com DDD. Ex.: (82) 99999-8888')
        return digitos

    def clean(self):
        dados = super().clean()
        lat, lng = dados.get('latitude'), dados.get('longitude')
        # a Vitrine é de Maceió: o ponto do mapa precisa cair na cidade
        if lat is not None and lng is not None and not (-9.78 <= float(lat) <= -9.40 and -35.90 <= float(lng) <= -35.55):
            self.add_error(None, 'O ponto marcado no mapa está fora de Maceió. Arraste o marcador até a sua loja.')
        # horário é opcional, mas se colocar um, precisa colocar os dois
        abre, fecha = dados.get('abre'), dados.get('fecha')
        if bool(abre) != bool(fecha):
            self.add_error('fecha' if abre else 'abre', 'Coloque a hora que abre e a hora que fecha.')
        elif abre and abre == fecha:
            self.add_error('fecha', 'A hora de fechar precisa ser diferente da hora de abrir.')
        if abre and fecha and not dados.get('dias'):
            self.add_error('dias', 'Marque os dias em que a loja abre.')
        return dados

    def clean_capa(self):
        return confere_foto(self.cleaned_data.get('capa'))

    def clean_cep(self):
        d = ''.join(c for c in self.cleaned_data.get('cep', '') if c.isdigit())
        if not d:
            return ''
        if len(d) != 8:
            raise forms.ValidationError('O CEP tem 8 números. Ex.: 57035-000')
        return f'{d[:5]}-{d[5:]}'
