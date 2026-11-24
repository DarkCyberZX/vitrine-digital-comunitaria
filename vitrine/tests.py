from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Banca, Produto, Venda


def cria_banca(usuario, **extra):
    user = get_user_model().objects.create_user(usuario, password='senha-teste-123')
    dados = dict(nome=f'Banca {usuario}', responsavel='Fulana, 40 anos', categoria='comida', bairro='Ponta Verde',
                 ponto='Orla', latitude=Decimal('-9.66'), longitude=Decimal('-35.70'), whatsapp='5582900000099')
    dados.update(extra)
    return Banca.objects.create(dono=user, **dados)


class TelasPublicasTests(TestCase):
    def setUp(self):
        self.b = cria_banca('ana')
        Produto.objects.create(banca=self.b, nome='Tapioca', preco=Decimal('8'))

    def test_inicio_lista_bancas(self):
        r = self.client.get(reverse('inicio'))
        self.assertContains(r, 'Banca ana')

    def test_banca_mostra_preco_e_whatsapp(self):
        r = self.client.get(reverse('banca', args=[self.b.pk]))
        self.assertContains(r, 'R$ 8,00')
        self.assertContains(r, 'https://wa.me/5582900000099?text=')

    def test_painel_exige_login(self):
        r = self.client.get(reverse('painel'))
        self.assertRedirects(r, reverse('login') + '?next=' + reverse('painel'))


class SegurancaPainelTests(TestCase):
    def setUp(self):
        self.ana = cria_banca('ana')
        self.beto = cria_banca('beto')
        self.prod_beto = Produto.objects.create(banca=self.beto, nome='Coco', preco=Decimal('6'))
        self.client.login(username='ana', password='senha-teste-123')

    def test_produto_vai_para_banca_de_quem_esta_logado(self):
        self.client.post(reverse('painel'), {'acao': 'produto', 'p-nome': 'Cuscuz', 'p-preco': '12,50',
                                             'p-tamanho': 'porção', 'p-disponibilidade': 'pronta',
                                             'p-banca': self.beto.pk})
        p = Produto.objects.get(nome='Cuscuz')
        self.assertEqual(p.banca, self.ana)
        self.assertEqual(p.preco, Decimal('12.50'))

    def test_nao_remove_produto_de_outra_banca(self):
        r = self.client.post(reverse('remover_produto', args=[self.prod_beto.pk]))
        self.assertEqual(r.status_code, 404)
        self.assertTrue(Produto.objects.filter(pk=self.prod_beto.pk).exists())

    def test_remover_exige_post(self):
        meu = Produto.objects.create(banca=self.ana, nome='Bolo', preco=Decimal('7'))
        r = self.client.get(reverse('remover_produto', args=[meu.pk]))
        self.assertEqual(r.status_code, 405)

    def _dados(self, **extra):
        d = {'acao': 'produto', 'p-nome': 'Bolo', 'p-preco': '9,00', 'p-tamanho': 'unidade', 'p-disponibilidade': 'pronta'}
        d.update(extra)
        return d

    def test_edita_o_proprio_produto(self):
        meu = Produto.objects.create(banca=self.ana, nome='Bolo', preco=Decimal('7'))
        r = self.client.get(reverse('painel') + f'?editar={meu.pk}')
        self.assertContains(r, '7,00')  # o preço aparece com vírgula no formulário
        self.client.post(reverse('painel'), self._dados(editar=meu.pk))
        meu.refresh_from_db()
        self.assertEqual(meu.preco, Decimal('9.00'))
        self.assertEqual(Produto.objects.filter(banca=self.ana).count(), 1)  # editou, não criou outro

    def test_nao_edita_produto_de_outra_banca(self):
        self.assertEqual(self.client.get(reverse('painel') + f'?editar={self.prod_beto.pk}').status_code, 404)
        r = self.client.post(reverse('painel'), self._dados(editar=self.prod_beto.pk, **{'p-nome': 'Invadido'}))
        self.assertEqual(r.status_code, 404)
        self.prod_beto.refresh_from_db()
        self.assertEqual(self.prod_beto.nome, 'Coco')

    def test_foto_valida_e_salva_com_nome_novo(self):
        import tempfile
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import override_settings
        png = b'\x89PNG\r\n\x1a\n' + b'\x00' * 64
        with tempfile.TemporaryDirectory() as pasta, override_settings(MEDIA_ROOT=pasta):
            self.client.post(reverse('painel'), self._dados(**{'p-imagem': SimpleUploadedFile('../../hack.png', png, 'image/png')}))
            p = Produto.objects.get(banca=self.ana, nome='Bolo')
            self.assertTrue(p.imagem.name.startswith('produtos/'))
            self.assertNotIn('hack', p.imagem.name)
            self.assertTrue(p.foto_url.endswith('.png'))

    def test_arquivo_que_nao_e_foto_e_recusado(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        falso = SimpleUploadedFile('foto.jpg', b'<script>alert(1)</script>', 'image/jpeg')
        r = self.client.post(reverse('painel'), self._dados(**{'p-imagem': falso}))
        self.assertContains(r, 'Envie uma foto em JPG, PNG ou WEBP.')
        self.assertFalse(Produto.objects.filter(banca=self.ana).exists())

    def test_resumo_mostra_nota_e_avaliacoes(self):
        from .models import Avaliacao
        Avaliacao.objects.create(banca=self.ana, nome='Rui', nota=4, comentario='Bom demais')
        r = self.client.get(reverse('painel'))
        self.assertContains(r, 'nota dos clientes')
        self.assertContains(r, 'Bom demais')

    def test_preco_invalido_e_recusado(self):
        self.client.post(reverse('painel'), {'acao': 'produto', 'p-nome': 'X', 'p-preco': '-3',
                                             'p-tamanho': 'un', 'p-disponibilidade': 'pronta'})
        self.assertFalse(Produto.objects.filter(nome='X').exists())

    def test_painel_mostra_aviso_do_pix_sem_botao_de_venda(self):
        r = self.client.get(reverse('painel'))
        self.assertContains(r, 'Confira o Pix antes de entregar')
        self.assertNotContains(r, 'Registrar uma venda')

    def test_csrf_obrigatorio(self):
        from django.test import Client
        c = Client(enforce_csrf_checks=True)
        c.login(username='ana', password='senha-teste-123')
        r = c.post(reverse('painel'), {'acao': 'historia', 'h-historia': 'hack'})
        self.assertEqual(r.status_code, 403)


class AvaliacaoTests(TestCase):
    def setUp(self):
        self.ana = cria_banca('ana')
        self.beto = cria_banca('beto')
        self.url = reverse('banca', args=[self.ana.pk])
        self.cliente = get_user_model().objects.create_user('maria', password='senha-teste-123', first_name='Maria')

    def entra(self, usuario='maria'):
        self.client.login(username=usuario, password='senha-teste-123')

    def test_sem_login_nao_avalia_e_vai_para_entrar(self):
        r = self.client.post(self.url, {'nota': '5', 'comentario': 'Spam'})
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse('login'), r['Location'])
        self.assertEqual(self.ana.avaliacoes.count(), 0)

    def test_cliente_avalia_com_nome_da_conta(self):
        self.entra()
        r = self.client.post(self.url, {'nota': '5', 'comentario': 'Ótima tapioca', 'nome': 'Outro Nome'}, follow=True)
        self.assertContains(r, 'Ótima tapioca')
        av = self.ana.avaliacoes.get()
        self.assertEqual((av.nome, av.autor), ('Maria', self.cliente))

    def test_uma_avaliacao_por_pessoa_segunda_vez_edita(self):
        self.entra()
        self.client.post(self.url, {'nota': '2', 'comentario': 'Primeira'})
        self.client.post(self.url, {'nota': '5', 'comentario': 'Mudei de ideia'})
        self.assertEqual(self.ana.avaliacoes.count(), 1)
        self.assertEqual(self.ana.avaliacoes.get().nota, 5)

    def test_banco_impede_duplicata(self):
        from django.db import IntegrityError, transaction
        from .models import Avaliacao
        Avaliacao.objects.create(banca=self.ana, autor=self.cliente, nome='Maria', nota=4, comentario='a')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Avaliacao.objects.create(banca=self.ana, autor=self.cliente, nome='Maria', nota=1, comentario='b')

    def test_dono_nao_avalia_a_propria_banca(self):
        self.entra('ana')
        self.client.post(self.url, {'nota': '5', 'comentario': 'Sou a melhor'})
        self.assertEqual(self.ana.avaliacoes.count(), 0)

    def test_banca_vem_da_url_nao_do_formulario(self):
        self.entra()
        self.client.post(self.url, {'nota': '4', 'comentario': 'Bom', 'banca': self.beto.pk})
        self.assertEqual((self.ana.avaliacoes.count(), self.beto.avaliacoes.count()), (1, 0))

    def test_nota_fora_de_1_a_5_recusada(self):
        self.entra()
        for nota in ('0', '6', 'abc', ''):
            self.client.post(self.url, {'nota': nota, 'comentario': 'Y'})
        self.assertEqual(self.ana.avaliacoes.count(), 0)

    def test_comentario_escondido_nao_aparece(self):
        from .models import Avaliacao
        Avaliacao.objects.create(banca=self.ana, nome='Troll', nota=1, comentario='texto ofensivo', visivel=False)
        self.assertNotContains(self.client.get(self.url), 'texto ofensivo')

    def test_html_no_comentario_e_escapado(self):
        self.entra()
        self.client.post(self.url, {'nota': '3', 'comentario': '<script>alert(1)</script>'})
        r = self.client.get(self.url)
        self.assertNotContains(r, '<script>alert(1)</script>')
        self.assertContains(r, '&lt;script&gt;')

    def test_media_na_home(self):
        from .models import Avaliacao
        Avaliacao.objects.create(banca=self.ana, nome='A', nota=5, comentario='x')
        Avaliacao.objects.create(banca=self.ana, nome='B', nota=4, comentario='y')
        self.assertContains(self.client.get(reverse('inicio')), '"media": 4.5')


class ContaTests(TestCase):
    def test_cadastro_cria_conta_e_entra(self):
        r = self.client.post(reverse('cadastro'), {'first_name': 'Joana', 'email': 'Joana@Exemplo.com',
                                                   'password1': 'feira-boa-2026', 'password2': 'feira-boa-2026',
                                                   'next': '/banca/1/'})
        self.assertRedirects(r, '/banca/1/', fetch_redirect_response=False)
        u = get_user_model().objects.get(first_name='Joana')
        self.assertEqual((u.username, u.email), ('joana@exemplo.com', 'joana@exemplo.com'))  # o e-mail vira o login
        self.assertIn('_auth_user_id', self.client.session)

    def test_cadastro_sem_campo_usuario_e_email_obrigatorio(self):
        r = self.client.get(reverse('cadastro'))
        self.assertNotContains(r, 'name="username"')
        r = self.client.post(reverse('cadastro'), {'first_name': 'X', 'email': '',
                                                   'password1': 'feira-boa-2026', 'password2': 'feira-boa-2026'})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(get_user_model().objects.exists())

    def test_cadastro_nao_redireciona_para_site_externo(self):
        r = self.client.post(reverse('cadastro'), {'first_name': 'X', 'email': 'x@exemplo.com', 'password1': 'feira-boa-2026',
                                                   'password2': 'feira-boa-2026', 'next': 'https://site-malicioso.com/'})
        self.assertRedirects(r, reverse('inicio'), fetch_redirect_response=False)

    def test_email_repetido_recusado(self):
        get_user_model().objects.create_user('a1', email='mesmo@exemplo.com', password='x-123456789')
        self.client.post(reverse('cadastro'), {'first_name': 'B', 'email': 'MESMO@exemplo.com',
                                               'password1': 'feira-boa-2026', 'password2': 'feira-boa-2026'})
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_entra_com_email_ou_usuario_antigo(self):
        get_user_model().objects.create_user('lia', email='lia@exemplo.com', password='senha-boa-2026')
        r = self.client.post(reverse('login'), {'username': 'LIA@exemplo.com', 'password': 'senha-boa-2026'})
        self.assertEqual(r.status_code, 302)
        self.client.logout()
        self.assertTrue(self.client.login(username='lia', password='senha-boa-2026'))  # contas antigas continuam
        self.client.logout()
        r = self.client.post(reverse('login'), {'username': 'lia@exemplo.com', 'password': 'errada-000'})
        self.assertContains(r, 'E-mail ou senha incorretos.')

    def test_esqueci_senha_manda_link_e_troca(self):
        from django.core import mail
        u = get_user_model().objects.create_user('lia', email='lia@exemplo.com', password='antiga-123456')
        self.client.post(reverse('password_reset'), {'email': 'lia@exemplo.com'})
        self.assertEqual(len(mail.outbox), 1)
        link = [l for l in mail.outbox[0].body.split() if '/senha/nova/' in l][0]
        caminho = link.split('://', 1)[1].split('/', 1)[1]
        r = self.client.get('/' + caminho, follow=True)
        r = self.client.post(r.redirect_chain[-1][0], {'new_password1': 'nova-senha-2026', 'new_password2': 'nova-senha-2026'})
        u.refresh_from_db()
        self.assertTrue(u.check_password('nova-senha-2026'))

    def test_email_inexistente_nao_revela_nada(self):
        from django.core import mail
        r = self.client.post(reverse('password_reset'), {'email': 'ninguem@exemplo.com'})
        self.assertRedirects(r, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 0)


class CadastroLojaTests(TestCase):
    """O comerciante cadastra a própria loja, sem aprovação."""
    DADOS = {'l-nome': 'Pastel da Joana', 'l-responsavel': 'Joana', 'l-categoria': 'comida', 'l-whatsapp': '(82) 98888-7777',
             'l-bairro': 'Ponta Verde', 'l-ponto': 'Rua Durval Guimarães', 'l-cep': '57035060',
             'l-latitude': '-9.662003', 'l-longitude': '-35.707900', 'l-historia': ''}
    CONTA = {'c-first_name': 'Joana', 'c-email': 'joana@exemplo.com', 'c-password1': 'Senha-forte-123', 'c-password2': 'Senha-forte-123'}

    def test_etapa_1_cria_so_a_conta_e_ja_entra(self):
        r = self.client.post(reverse('cadastro_loja'), self.CONTA)
        self.assertRedirects(r, reverse('cadastro_loja'))
        self.assertTrue(get_user_model().objects.filter(username='joana@exemplo.com').exists())
        self.assertFalse(Banca.objects.exists())
        self.assertContains(self.client.get(reverse('cadastro_loja')), 'Etapa 2')  # já logada, vê os dados da loja

    def test_etapa_2_cria_a_loja_e_aparece_na_hora(self):
        self.client.post(reverse('cadastro_loja'), self.CONTA)
        r = self.client.post(reverse('cadastro_loja'), self.DADOS)
        self.assertRedirects(r, reverse('painel'))
        loja = Banca.objects.get(nome='Pastel da Joana')
        self.assertEqual(loja.dono.username, 'joana@exemplo.com')
        self.assertEqual(loja.whatsapp, '5582988887777')  # número limpo, com 55
        self.assertEqual(loja.cep, '57035-060')
        self.assertTrue(loja.visivel)  # sem esperar aprovação
        self.assertContains(self.client.get(reverse('inicio')), 'Pastel da Joana')

    def test_loja_sem_local_no_mapa_nao_e_criada(self):
        self.client.post(reverse('cadastro_loja'), self.CONTA)
        r = self.client.post(reverse('cadastro_loja'), {**self.DADOS, 'l-latitude': ''})
        self.assertContains(r, 'Marque no mapa')
        self.assertFalse(Banca.objects.exists())

    def test_horario_de_funcionamento_aparece_na_loja(self):
        self.client.post(reverse('cadastro_loja'), self.CONTA)
        self.client.post(reverse('cadastro_loja'), {**self.DADOS, 'l-dias': 'seg_sab', 'l-abre': '07:00', 'l-fecha': '18:30'})
        loja = Banca.objects.get(nome='Pastel da Joana')
        self.assertEqual(loja.horario_texto, 'Segunda a sábado, das 7h às 18h30')
        self.assertContains(self.client.get(reverse('banca', args=[loja.pk])), 'das 7h às 18h30')

    def test_horario_pela_metade_e_recusado(self):
        self.client.post(reverse('cadastro_loja'), self.CONTA)
        r = self.client.post(reverse('cadastro_loja'), {**self.DADOS, 'l-abre': '07:00'})
        self.assertContains(r, 'Coloque a hora que abre e a hora que fecha.')
        self.assertFalse(Banca.objects.exists())

    def test_local_fora_de_maceio_e_recusado(self):
        self.client.post(reverse('cadastro_loja'), self.CONTA)
        r = self.client.post(reverse('cadastro_loja'), {**self.DADOS, 'l-latitude': '-23.55', 'l-longitude': '-46.63'})
        self.assertContains(r, 'fora de Maceió')
        self.assertFalse(Banca.objects.filter(nome='Pastel da Joana').exists())

    def test_cliente_logado_cria_so_a_loja(self):
        get_user_model().objects.create_user('maria', password='senha-teste-123')
        self.client.login(username='maria', password='senha-teste-123')
        self.client.post(reverse('cadastro_loja'), self.DADOS)
        self.assertEqual(Banca.objects.get(nome='Pastel da Joana').dono.username, 'maria')

    def test_quem_ja_tem_loja_vai_para_o_painel(self):
        cria_banca('ana'); self.client.login(username='ana', password='senha-teste-123')
        self.assertRedirects(self.client.get(reverse('cadastro_loja')), reverse('painel'))

    def test_dono_nao_vem_do_formulario(self):
        outro = get_user_model().objects.create_user('beto', password='senha-teste-123')
        self.client.post(reverse('cadastro_loja'), self.CONTA)
        self.client.post(reverse('cadastro_loja'), {**self.DADOS, 'l-dono': outro.pk})
        self.assertEqual(Banca.objects.get(nome='Pastel da Joana').dono.username, 'joana@exemplo.com')

    def test_painel_sem_loja_manda_cadastrar(self):
        get_user_model().objects.create_user('maria', password='senha-teste-123')
        self.client.login(username='maria', password='senha-teste-123')
        self.assertRedirects(self.client.get(reverse('painel')), reverse('cadastro_loja'))

    def test_edita_os_dados_da_propria_loja(self):
        ana = cria_banca('ana'); self.client.login(username='ana', password='senha-teste-123')
        self.client.post(reverse('editar_loja'), {**self.DADOS, 'l-nome': 'Novo nome'})
        ana.refresh_from_db()
        self.assertEqual(ana.nome, 'Novo nome')

    def test_loja_escondida_pelo_admin_some_do_site(self):
        ana = cria_banca('ana', visivel=False)
        self.assertNotContains(self.client.get(reverse('inicio')), ana.nome)
        self.assertEqual(self.client.get(reverse('banca', args=[ana.pk])).status_code, 404)


class ComoChegarTests(TestCase):
    def test_link_do_google_maps_usa_ponto_decimal(self):
        # em português o Django escreve "-9,66"; o Google Maps leria a vírgula como separador e erraria o lugar
        loja = cria_banca('ana', latitude=Decimal('-9.664100'), longitude=Decimal('-35.701700'))
        r = self.client.get(reverse('banca', args=[loja.pk]))
        self.assertContains(r, 'destination=-9.664100,-35.701700')


class DescricaoProdutoTests(TestCase):
    def test_descricao_salva_aparece_e_e_lida(self):
        ana = cria_banca('ana'); self.client.login(username='ana', password='senha-teste-123')
        self.client.post(reverse('painel'), {'acao': 'produto', 'p-nome': 'Cocada', 'p-preco': '4', 'p-tamanho': 'unidade',
                                             'p-disponibilidade': 'pronta', 'p-descricao': 'Feita com coco fresco.'})
        self.assertEqual(Produto.objects.get(nome='Cocada').descricao, 'Feita com coco fresco.')
        r = self.client.get(reverse('banca', args=[ana.pk]))
        self.assertContains(r, 'Feita com coco fresco.')

    def test_descricao_longa_demais_e_recusada(self):
        cria_banca('ana'); self.client.login(username='ana', password='senha-teste-123')
        r = self.client.post(reverse('painel'), {'acao': 'produto', 'p-nome': 'Cocada', 'p-preco': '4', 'p-tamanho': 'unidade',
                                                 'p-disponibilidade': 'pronta', 'p-descricao': 'x' * 201})
        self.assertFalse(Produto.objects.filter(nome='Cocada').exists())
