"""Cria bancas e produtos fictícios para demonstração.

Uso: python manage.py popular_demo

Contas de teste criadas (só para o protótipo, nunca use em produção):
  - comerciantes: usuário = cida, ze, lucia, rafa, nena, marcos, graca + 30 lojas extras (_lojas_extras.py)
  - cliente (para avaliar): usuário = cliente
  - administrador: usuário = admin

As senhas NÃO ficam no código. Defina antes de rodar:
  VITRINE_SENHA_DEMO   senha das contas de comerciante e do cliente
  VITRINE_SENHA_ADMIN  senha do admin
Sem elas, o comando sorteia uma senha e mostra no terminal (só para contas que ainda não existem).
"""
import os
import secrets
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from vitrine.models import Avaliacao, Banca, Produto

SENHA_DEMO = os.environ.get('VITRINE_SENHA_DEMO') or secrets.token_urlsafe(12)
SENHA_ADMIN = os.environ.get('VITRINE_SENHA_ADMIN') or secrets.token_urlsafe(16)

BANCAS = [
    dict(usuario='cida', foto='vitrine/fotos/capa-cida.jpg', nome='Tapiocaria da Cida', responsavel='Aparecida (Dona Cida)', categoria='comida',
         emoji='🫓', cor='#fde68a', bairro='Ponta Verde', ponto='Orla de Ponta Verde', cep='57035',
         latitude='-9.664100', longitude='-35.701700', aberta=True, whatsapp='5582900000001',
         historia='Faço tapioca há 20 anos com a goma que eu mesma preparo. Aprendi com minha mãe em Marechal '
                  'Deodoro e hoje é daqui que sai o sustento da casa.',
         produtos=[('Tapioca de queijo coalho', 'unidade', '8', 'pronta', '🧀'),
                   ('Tapioca de coco com leite condensado', 'unidade', '10', 'pronta', '🥥'),
                   ('Cuscuz recheado', 'porção', '12', 'pronta', '🌽'),
                   ('Goma fresca', '1 kg', '9', 'encomenda', '🥣')]),
    dict(usuario='ze', foto='vitrine/fotos/capa-ze.jpg', nome='Coco Gelado do Seu Zé', responsavel='José', categoria='frutas',
         emoji='🥥', cor='#bbf7d0', bairro='Ponta Verde', ponto='Orla, próximo ao farol', cep='57035',
         latitude='-9.663950', longitude='-35.703300', aberta=True, whatsapp='5582900000002',
         historia='Vendo coco na orla desde 1998. Os cocos vêm de um sítio da família em Barra de São Miguel, '
                  'colhidos na semana.',
         produtos=[('Coco verde gelado', 'unidade', '6', 'pronta', '🥥'),
                   ('Água de coco', 'garrafa 1 L', '12', 'pronta', '🧃'),
                   ('Cocada caseira', 'unidade', '4', 'pronta', '🍬')]),
    dict(usuario='lucia', foto='vitrine/fotos/capa-lucia.jpg', nome='Renda Filé da Lúcia', responsavel='Lúcia', categoria='artesanato',
         emoji='🧶', cor='#fecdd3', bairro='Pajuçara', ponto='Feira de artesanato', cep='57030',
         latitude='-9.668900', longitude='-35.714200', aberta=True, whatsapp='5582900000003',
         historia='Bordo filé como aprendi com as rendeiras do Pontal da Barra. Cada toalha leva de uma a três '
                  'semanas de trabalho, ponto por ponto.',
         produtos=[('Toalha de mesa em filé', '1,40 m', '180', 'encomenda', '🧵'),
                   ('Jogo americano', '4 peças', '90', 'pronta', '🍽️'),
                   ('Bolsa de palha', 'média', '65', 'pronta', '👜'),
                   ('Chaveiro bordado', 'unidade', '10', 'pronta', '🔑')]),
    dict(usuario='rafa', foto='vitrine/fotos/capa-brecho.jpg', nome='Brechó Achadinhos', responsavel='Rafa', categoria='roupas',
         emoji='👗', cor='#ddd6fe', bairro='Jatiúca', ponto='Rua próxima à praça', cep='57036',
         latitude='-9.652200', longitude='-35.706900', aberta=False, whatsapp='5582900000004',
         historia='Comecei vendendo minhas roupas para pagar a faculdade. Hoje garimpo peças boas e conservadas '
                  'para dar uma segunda vida a elas.',
         produtos=[('Vestido floral', 'M', '35', 'pronta', '👗'),
                   ('Camisa de linho', 'G', '40', 'pronta', '👔'),
                   ('Sandália de couro', '37', '30', 'pronta', '👡')]),
    dict(usuario='nena', foto='vitrine/fotos/capa-nena.jpg', nome='Doces da Vó Nena', responsavel='Neném', categoria='comida',
         emoji='🍰', cor='#fed7aa', bairro='Pajuçara', ponto='Vila de alimentos', cep='57030',
         latitude='-9.666000', longitude='-35.712500', aberta=True, whatsapp='5582900000005',
         historia='Bolo de rolo e bolo de macaxeira com as receitas da minha avó. Minha neta me ajuda com o celular.',
         produtos=[('Bolo de macaxeira', 'fatia', '7', 'pronta', '🍰'),
                   ('Bolo de rolo', 'inteiro', '45', 'encomenda', '🥮'),
                   ('Pé de moleque', 'unidade', '5', 'pronta', '🥜')]),
    dict(usuario='marcos', foto='vitrine/fotos/capa-barro.jpg', nome='Cerâmica Barro Vivo', responsavel='Marcos', categoria='artesanato',
         emoji='🏺', cor='#e7d3c0', bairro='Ponta Verde', ponto='Feira de artesanato', cep='57035',
         latitude='-9.662700', longitude='-35.704600', aberta=True, whatsapp='5582900000006',
         historia='Modelo peças de barro inspiradas nos bonecos do interior de Alagoas. Queimo tudo em forno a '
                  'lenha no quintal.',
         produtos=[('Vaso de barro', 'médio', '55', 'pronta', '🏺'),
                   ('Boneco de barro', '15 cm', '40', 'pronta', '🗿'),
                   ('Peça personalizada', 'sob medida', '120', 'encomenda', '🎨')]),
    dict(usuario='graca', foto='vitrine/fotos/capa-costura.jpg', nome='Costura da Dona Graça', responsavel='Graça', categoria='servicos',
         emoji='✂️', cor='#c7d2fe', bairro='Jatiúca', ponto='Rua de trás do mercadinho', cep='57036',
         latitude='-9.649800', longitude='-35.709900', aberta=True, whatsapp='5582900000007',
         historia='Costuro há 30 anos. Faço bainha, ajuste e conserto na hora ou de um dia para o outro, '
                  'com o preço combinado antes.',
         produtos=[('Bainha de calça', 'por peça', '15', 'pronta', '🧵'),
                   ('Ajuste de roupa', 'por peça', '25', 'pronta', '📏'),
                   ('Troca de zíper', 'por peça', '20', 'encomenda', '🤐')]),
]


# fotos: Unsplash (licença Unsplash, uso livre)
FOTOS = {'Tapioca de queijo coalho': 'tapioca-queijo', 'Tapioca de coco com leite condensado': 'tapioca-coco', 'Cuscuz recheado': 'cuscuz', 'Goma fresca': 'goma', 'Coco verde gelado': 'coco-verde', 'Água de coco': 'agua-coco', 'Cocada caseira': 'cocada', 'Toalha de mesa em filé': 'toalha-file', 'Jogo americano': 'jogo-americano', 'Bolsa de palha': 'bolsa-palha', 'Chaveiro bordado': 'chaveiro', 'Vestido floral': 'vestido', 'Camisa de linho': 'camisa-linho', 'Sandália de couro': 'sandalia', 'Bolo de macaxeira': 'bolo-macaxeira', 'Bolo de rolo': 'bolo-rolo', 'Pé de moleque': 'pe-moleque', 'Vaso de barro': 'vaso-barro', 'Boneco de barro': 'boneco-barro', 'Peça personalizada': 'peca-personalizada', 'Bainha de calça': 'bainha', 'Ajuste de roupa': 'ajuste-roupa', 'Troca de zíper': 'ziper'}

# avaliações FICTÍCIAS, só para demonstrar o protótipo
AVALIACOES = {
    'cida': [('Marta S.', 5, 'Melhor tapioca da orla! A goma é fresquinha e a Dona Cida é um amor.'),
             ('Rafael', 5, 'Vi o preço aqui antes de ir e foi exatamente aquele. Recomendo a de coco.'),
             ('Joana P.', 4, 'Muito boa, só demorou um pouco porque tinha fila no fim da tarde.'),
             ('Seu Antônio', 5, 'Encomendei goma pelo WhatsApp e ela separou certinho.')],
    'ze': [('Bruna', 5, 'Coco geladíssimo e o Seu Zé é muito simpático.'),
           ('Lucas M.', 4, 'Bom preço para a orla. A cocada é ótima também.'),
           ('Ana Clara', 5, 'Água de coco na garrafa salvou meu dia de praia.')],
    'lucia': [('Fernanda', 5, 'A toalha de filé ficou linda na minha mesa, trabalho impecável.'),
              ('Carla R.', 5, 'Comprei de presente e a pessoa amou. Dá para ver o capricho.'),
              ('Pedro', 4, 'Peças lindas. A de encomenda levou duas semanas, como ela avisou.')],
    'rafa': [('Thaís', 4, 'Achei um vestido ótimo por um preço justo.'),
             ('Gabriel', 4, 'Roupas conservadas e bem organizadas. Vale a visita.'),
             ('Débora', 3, 'Gostei, mas estava fechado no dia que fui. Melhor combinar antes.')],
    'nena': [('Paulo H.', 5, 'Bolo de macaxeira igual ao da minha avó.'),
             ('Renata', 5, 'O bolo de rolo de encomenda chegou perfeito para o aniversário.'),
             ('Igor', 5, 'Doces caseiros de verdade, e a Dona Neném é uma figura!'),
             ('Larissa', 4, 'Pé de moleque delicioso, só acho que podia ter mais.')],
    'graca': [('Cláudia', 5, 'Fez a bainha da minha calça em 20 minutos, ficou perfeita.'),
              ('Roberto', 4, 'Trocou o zíper da jaqueta pelo preço combinado. Recomendo.'),
              ('Aline', 5, 'Ajustou meu vestido de formatura, ficou sob medida.')],
    'marcos': [('Helena', 5, 'Vaso lindo, e o Marcos explicou todo o processo do forno a lenha.'),
               ('Vinícius', 4, 'Encomendei uma peça personalizada e ficou do jeito que pedi.'),
               ('Sônia', 5, 'Artesanato alagoano de verdade. Comprei três bonecos.')],
}


# mais 30 lojas fictícias espalhadas por Maceió (arquivo separado para não misturar com as 7 originais)
from ._lojas_extras import LOJAS_EXTRAS, avaliacoes_extras  # noqa: E402
from ._descricoes import DESCRICOES  # noqa: E402
BANCAS = BANCAS + LOJAS_EXTRAS
AVALIACOES = {**AVALIACOES, **avaliacoes_extras()}


class Command(BaseCommand):
    help = 'Cria bancas, produtos e contas de teste fictícios para demonstrar o protótipo.'

    @transaction.atomic
    def handle(self, *args, **opts):
        User = get_user_model()
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', '', SENHA_ADMIN)
            if not os.environ.get('VITRINE_SENHA_ADMIN'):
                self.stdout.write(f'Senha sorteada do admin: {SENHA_ADMIN}')
        if not os.environ.get('VITRINE_SENHA_DEMO') and not User.objects.filter(username='cliente').exists():
            self.stdout.write(f'Senha sorteada das contas de demonstração: {SENHA_DEMO}')
        if not User.objects.filter(username='cliente').exists():
            User.objects.create_user('cliente', 'cliente@exemplo.com', SENHA_DEMO, first_name='Maria')

        for dados in BANCAS:
            dados = dict(dados)
            usuario = dados.pop('usuario')
            produtos = dados.pop('produtos')
            user, criado = User.objects.get_or_create(username=usuario)
            if criado:
                user.set_password(SENHA_DEMO)
                user.save()
            banca, _ = Banca.objects.update_or_create(dono=user, defaults=dados)
            if user.first_name != banca.primeiro_nome:
                user.first_name = banca.primeiro_nome
                user.save(update_fields=["first_name"])
            banca.produtos.all().delete()
            for nome, tam, preco, disp, emoji, *foto_propria in produtos:
                foto = foto_propria[0] if foto_propria else (f'vitrine/fotos/{FOTOS[nome]}.jpg' if nome in FOTOS else '')
                Produto.objects.create(banca=banca, nome=nome, tamanho=tam, preco=Decimal(preco), descricao=DESCRICOES.get(nome, ''),
                                       disponibilidade=disp, emoji=emoji or '📦', foto=foto)
            banca.avaliacoes.all().delete()
            for nome, nota, comentario in AVALIACOES.get(usuario, []):
                Avaliacao.objects.create(banca=banca, nome=nome, nota=nota, comentario=comentario)

        self.stdout.write(self.style.SUCCESS(f'{len(BANCAS)} lojas de demonstração prontas.'))
