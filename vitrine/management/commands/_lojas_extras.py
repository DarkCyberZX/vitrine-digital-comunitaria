"""Mais 30 lojas FICTÍCIAS para deixar o protótipo com cara de site em uso.

Nomes, telefones, histórias e avaliações são inventados. As fotos são do Unsplash (já usadas no projeto).
Formato igual ao de BANCAS em popular_demo.py.
"""
import random


def _p(nome, tam, preco, disp='pronta'):
    return (nome, tam, str(preco), disp, '')


def _loja(usuario, nome, resp, cat, bairro, ponto, cep, lat, lng, capa, historia, produtos, aberta=True):
    return dict(usuario=usuario, nome=nome, responsavel=resp, categoria=cat, bairro=bairro, ponto=ponto, cep=cep,
                latitude=f'{lat:.6f}', longitude=f'{lng:.6f}', aberta=aberta,
                foto=f'vitrine/fotos/{capa}.jpg' if capa else '', emoji='🛍️', cor=CORES[cat],
                whatsapp='', historia=historia, produtos=produtos)


CORES = {'comida': '#fde68a', 'frutas': '#bbf7d0', 'artesanato': '#fecdd3', 'roupas': '#ddd6fe', 'servicos': '#bae6fd'}

LOJAS_EXTRAS = [
    # ---------- comida e doces ----------
    _loja('socorro', 'Cuscuz da Socorro', 'Socorro', 'comida', 'Jatiúca', 'Perto da feirinha da Jatiúca', '57036-000',
          -9.6478, -35.7092, 'cuscuz', 'Cuscuz de milho ralado na hora, recheado com o que o cliente pedir. Café da manhã desde as 6h.',
          [_p('Cuscuz recheado', 'porção', 12), _p('Tapioca de queijo coalho', 'unidade', 9), _p('Café coado', 'copo', 3)]),
    _loja('dete', 'Bolos da Dete', 'Bernadete (Dete)', 'comida', 'Farol', 'Rua do colégio, casa amarela', '57051-000',
          -9.6522, -35.7348, 'bolo-rolo', 'Faço bolo de rolo fininho como manda a tradição pernambucana que aprendi com minha sogra.',
          [_p('Bolo de rolo', 'fatia', 8), _p('Bolo de rolo inteiro', '1 kg', 60, 'encomenda'), _p('Bolo de macaxeira', 'fatia', 7)]),
    _loja('tonho', 'Tapioca do Tonho', 'Antônio (Tonho)', 'comida', 'Pajuçara', 'Calçadão, em frente à feira', '57030-170',
          -9.6688, -35.7163, 'tapioca-queijo', 'Tapioqueiro há 15 anos. A goma eu compro direto de uma casa de farinha de Arapiraca.',
          [_p('Tapioca de queijo coalho', 'unidade', 8), _p('Tapioca de coco com leite condensado', 'unidade', 10), _p('Tapioca de carne de sol', 'unidade', 14)]),
    _loja('fatima', 'Cocadas da Fátima', 'Fátima', 'comida', 'Centro', 'Calçadão do Comércio', '57020-000',
          -9.6655, -35.7352, 'cocada', 'Cocada de forno, de colher e queimada. Faço em panela de cobre, do jeito da minha mãe.',
          [_p('Cocada caseira', 'unidade', 4), _p('Cocada de forno', 'unidade', 5), _p('Pé de moleque', 'unidade', 4)]),
    _loja('irene', 'Doceria da Irene', 'Irene', 'comida', 'Poço', 'Perto da praça do Poço', '57025-000',
          -9.6596, -35.7245, 'pe-moleque', 'Doces de festa por encomenda: brigadeiro, cajuzinho e pé de moleque para aniversário.',
          [_p('Pé de moleque', 'unidade', 4), _p('Cento de docinhos', '100 un.', 90, 'encomenda'), _p('Bolo de macaxeira', 'fatia', 7)]),
    _loja('jose_goma', 'Goma do Seu Biu', 'Severino (Seu Biu)', 'comida', 'Levada', 'Mercado da Produção, box 12', '57017-000',
          -9.6672, -35.7438, 'goma', 'Vendo goma e farinha no Mercado da Produção há 30 anos. Tudo vem do interior toda semana.',
          [_p('Goma fresca', '1 kg', 8), _p('Farinha de mandioca', '1 kg', 7), _p('Beiju', 'pacote', 6)]),
    _loja('lene', 'Quentinhas da Lene', 'Marilene (Lene)', 'comida', 'Jacintinho', 'Rua principal, perto do posto de saúde', '57040-000',
          -9.6408, -35.7208, '', 'Almoço caseiro com feijão de corda, macaxeira e carne de sol. Entrego no bairro.',
          [_p('Quentinha de carne de sol', 'marmita', 18), _p('Quentinha de frango', 'marmita', 16), _p('Suco de cajá', '500 ml', 5)]),
    _loja('bia_bolos', 'Bia Bolos Caseiros', 'Beatriz (Bia)', 'comida', 'Gruta de Lourdes', 'Próximo à igreja da Gruta', '57052-000',
          -9.6305, -35.7275, 'bolo-macaxeira', 'Sou estudante e faço bolos no fim de semana para ajudar em casa.',
          [_p('Bolo de macaxeira', 'fatia', 6), _p('Bolo de milho', 'fatia', 6), _p('Bolo de rolo', 'fatia', 8)]),
    _loja('neide', 'Tapiocaria da Neide', 'Neide', 'comida', 'Cruz das Almas', 'Avenida, perto da praia', '57038-000',
          -9.6352, -35.7046, 'tapioca-coco', 'Tapioca de coco feita com coco ralado na hora. A mais pedida é a de coco com queijo.',
          [_p('Tapioca de coco com leite condensado', 'unidade', 10), _p('Tapioca de queijo coalho', 'unidade', 8), _p('Cuscuz recheado', 'porção', 12)]),
    _loja('ana_acai', 'Sururu da Ana', 'Ana', 'comida', 'Trapiche da Barra', 'Beira da lagoa, perto do campo', '57010-000',
          -9.6725, -35.7575, '', 'Caldinho de sururu catado na lagoa Mundaú, receita da minha família de marisqueiras.',
          [_p('Caldinho de sururu', 'copo', 8), _p('Sururu de capote', 'porção', 25, 'encomenda')], aberta=False),

    # ---------- frutas e coco ----------
    _loja('chico', 'Frutas do Chico', 'Francisco (Chico)', 'frutas', 'Levada', 'Mercado da Produção, box 40', '57017-000',
          -9.6683, -35.7425, 'agua-coco', 'Frutas da estação direto do produtor: cajá, mangaba, pinha e caju.',
          [_p('Água de coco', 'garrafa 1 L', 10), _p('Polpa de cajá', '1 kg', 15), _p('Mangaba', '1 kg', 12)]),
    _loja('dinho', 'Coco do Dinho', 'Claudinho (Dinho)', 'frutas', 'Jatiúca', 'Orla da Jatiúca, quiosque azul', '57036-000',
          -9.6505, -35.7058, 'coco-verde', 'Coco gelado e água de coco engarrafada na hora, sem conservante.',
          [_p('Coco verde gelado', 'unidade', 6), _p('Água de coco', 'garrafa 1 L', 12)]),
    _loja('rita', 'Hortifruti da Rita', 'Rita', 'frutas', 'Feitosa', 'Esquina da padaria', '57043-000',
          -9.6285, -35.7212, '', 'Verduras e frutas fresquinhas. Monto cesta da semana e entrego de bicicleta.',
          [_p('Cesta de frutas da semana', 'cesta', 35, 'encomenda'), _p('Banana prata', 'dúzia', 7), _p('Polpa de cajá', '1 kg', 15)]),
    _loja('cosme', 'Caldo de Cana do Cosme', 'Cosme', 'frutas', 'Centro', 'Praça Deodoro', '57020-000',
          -9.6672, -35.7368, 'agua-coco', 'Caldo de cana moído na hora, com limão ou abacaxi.',
          [_p('Caldo de cana', 'copo 500 ml', 6), _p('Água de coco', 'garrafa 1 L', 11)]),
    _loja('vera', 'Polpas da Vera', 'Vera', 'frutas', 'Serraria', 'Conjunto, rua 5', '57046-000',
          -9.5928, -35.7186, '', 'Polpa de fruta congelada feita em casa, sem açúcar: cajá, acerola, goiaba e maracujá.',
          [_p('Polpa de cajá', '1 kg', 14), _p('Polpa de acerola', '1 kg', 12), _p('Polpa de goiaba', '1 kg', 12)]),

    # ---------- artesanato ----------
    _loja('cicera', 'Filé da Cícera', 'Cícera', 'artesanato', 'Pontal da Barra', 'Rua das rendeiras', '57010-000',
          -9.6930, -35.7756, 'toalha-file', 'Rendeira do Pontal desde menina. O filé é patrimônio de Alagoas e eu ensino minhas netas.',
          [_p('Toalha de mesa em filé', '1,40 m', 170, 'encomenda'), _p('Jogo americano', '4 peças', 85), _p('Caminho de mesa em filé', '1 m', 75)]),
    _loja('mariazinha', 'Rendas da Mariazinha', 'Maria (Mariazinha)', 'artesanato', 'Pontal da Barra', 'Feirinha do Pontal', '57010-000',
          -9.6944, -35.7769, 'jogo-americano', 'Faço jogo americano e centro de mesa em filé colorido.',
          [_p('Jogo americano', '4 peças', 90), _p('Chaveiro bordado', 'unidade', 10)]),
    _loja('joao_barro', 'Barro do Mestre João', 'João', 'artesanato', 'Bebedouro', 'Ateliê no fundo do quintal', '57017-000',
          -9.6215, -35.7540, 'vaso-barro', 'Mestre ceramista. Aprendi a modelar barro com os artesãos do São Francisco.',
          [_p('Vaso de barro', 'médio', 55), _p('Boneco de barro', 'unidade', 35), _p('Peça personalizada', 'sob medida', 120, 'encomenda')]),
    _loja('dani', 'Palha & Arte da Dani', 'Daniela (Dani)', 'artesanato', 'Ponta Verde', 'Feira de artesanato da orla', '57035-000',
          -9.6628, -35.7072, 'bolsa-palha', 'Bolsas e chapéus de palha de ouricuri trançados à mão.',
          [_p('Bolsa de palha', 'média', 60), _p('Chapéu de palha', 'unidade', 35)]),
    _loja('ze_madeira', 'Madeira do Zé Pequeno', 'José (Zé Pequeno)', 'artesanato', 'Jaraguá', 'Perto do Museu Théo Brandão', '57022-000',
          -9.6700, -35.7268, 'peca-personalizada', 'Esculpo barcos e jangadas em madeira de reaproveitamento.',
          [_p('Jangada de madeira', 'pequena', 45), _p('Peça personalizada', 'sob medida', 150, 'encomenda'), _p('Chaveiro de madeira', 'unidade', 8)]),
    _loja('kel', 'Bonecas da Kel', 'Raquel (Kel)', 'artesanato', 'Benedito Bentes', 'Rua da escola estadual', '57084-000',
          -9.5508, -35.7232, 'boneco-barro', 'Bonecas de pano e de barro com roupas de chita, feitas com retalhos doados.',
          [_p('Boneco de barro', 'unidade', 30), _p('Boneca de pano', 'unidade', 40)]),
    _loja('luiz', 'Chaveiros do Luiz', 'Luiz', 'artesanato', 'Tabuleiro do Martins', 'Feira do Tabuleiro, sábado', '57081-000',
          -9.5815, -35.7548, 'chaveiro', 'Chaveiros e lembrancinhas personalizados para festa e casamento.',
          [_p('Chaveiro bordado', 'unidade', 8), _p('Lembrancinha personalizada', '10 un.', 45, 'encomenda')]),

    # ---------- roupas e brechó ----------
    _loja('carol', 'Brechó da Carol', 'Carolina (Carol)', 'roupas', 'Ponta Verde', 'Rua de dentro, perto da padaria', '57035-000',
          -9.6608, -35.7095, 'vestido', 'Brechó com peças selecionadas, lavadas e passadas. Troco peça por peça.',
          [_p('Vestido floral', 'P', 30), _p('Saia jeans', '38', 25), _p('Sandália de couro', '36', 28)]),
    _loja('moda_lia', 'Moda Praia da Lia', 'Lia', 'roupas', 'Pajuçara', 'Galeria da orla, loja 3', '57030-000',
          -9.6660, -35.7148, 'camisa-linho', 'Costuro biquínis e saídas de praia com tecido estampado de Alagoas.',
          [_p('Saída de praia', 'única', 45), _p('Camisa de linho', 'M', 55), _p('Biquíni sob medida', 'sob medida', 70, 'encomenda')]),
    _loja('tiago', 'Sandálias do Tiago', 'Tiago', 'roupas', 'Centro', 'Rua do Comércio, banca 8', '57020-000',
          -9.6648, -35.7362, 'sandalia', 'Sandálias de couro feitas por artesãos do sertão.',
          [_p('Sandália de couro', '38', 35), _p('Sandália de couro infantil', '28', 25)]),
    _loja('jessica', 'Achados da Jéssica', 'Jéssica', 'roupas', 'Mangabeiras', 'Prédio azul, portaria', '57037-000',
          -9.6472, -35.7176, '', 'Roupas infantis seminovas. Mãe de três, sei o quanto criança cresce rápido!',
          [_p('Conjunto infantil', '4 anos', 20), _p('Vestido infantil', '6 anos', 18)], aberta=False),

    # ---------- serviços ----------
    _loja('edna', 'Costuras da Edna', 'Edna', 'servicos', 'Jacintinho', 'Ladeira, casa verde', '57040-000',
          -9.6390, -35.7225, 'ajuste-roupa', 'Costureira há 25 anos. Faço ajuste, barra e reforma de roupa.',
          [_p('Ajuste de roupa', 'peça', 20), _p('Bainha de calça', 'peça', 12)]),
    _loja('fabio', 'Conserta Tudo do Fábio', 'Fábio', 'servicos', 'Farol', 'Garagem ao lado da farmácia', '57051-000',
          -9.6540, -35.7330, '', 'Conserto ventilador, liquidificador e ferro de passar. Orçamento sem compromisso.',
          [_p('Conserto de ventilador', 'serviço', 40), _p('Conserto de liquidificador', 'serviço', 35)]),
    _loja('marta', 'Zíper e Barra da Marta', 'Marta', 'servicos', 'Gruta de Lourdes', 'Rua de trás do mercadinho', '57052-000',
          -9.6340, -35.7300, 'ziper', 'Troco zíper de calça, mochila e jaqueta na hora.',
          [_p('Troca de zíper', 'peça', 15), _p('Bainha de calça', 'peça', 12)]),
    _loja('sueli', 'Ateliê da Sueli', 'Sueli', 'servicos', 'Stella Maris', 'Rua paralela à praia', '57039-000',
          -9.6172, -35.6968, 'bainha', 'Ajustes finos e roupas sob medida para festa.',
          [_p('Ajuste de roupa', 'peça', 25), _p('Vestido sob medida', 'sob medida', 220, 'encomenda')]),
]

_COMENTARIOS = {
    'comida': ['Tudo fresquinho e muito saboroso.', 'Preço justo e atendimento rápido.', 'Comprei de novo, vale muito a pena!',
               'Igual ao da minha avó.', 'Encomendei pelo WhatsApp e chegou certinho.', 'Bom, mas tinha fila no horário do almoço.'],
    'frutas': ['Frutas bonitas e bem geladas.', 'Ótimo preço, melhor que no supermercado.', 'Atendimento muito simpático.',
               'A polpa é bem concentrada, rende muito.', 'Sempre fresco.'],
    'artesanato': ['Trabalho lindo, feito com muito capricho.', 'Comprei de presente e fez sucesso.', 'Artesanato alagoano de verdade.',
                   'A encomenda chegou no prazo combinado.', 'Peças únicas, vale cada centavo.'],
    'roupas': ['Peças conservadas e preço bom.', 'Achei exatamente o que procurava.', 'Atendimento atencioso, deixou provar com calma.',
               'Gostei, mas o tamanho veio um pouco grande.'],
    'servicos': ['Serviço rápido e bem feito.', 'Cobrou o que combinou, recomendo.', 'Ficou perfeito, voltarei mais vezes.',
                 'Muito caprichosa, ajuste ficou sob medida.'],
}
_NOMES = ['Carla', 'Jorge', 'Patrícia', 'Diego', 'Luana', 'Marcos V.', 'Simone', 'Rodrigo', 'Tânia', 'Felipe', 'Aline M.',
          'Bruno', 'Cecília', 'Eduardo', 'Gisele', 'Hugo', 'Ivone', 'Júlia', 'Kátia', 'Leandro', 'Mônica', 'Nádia', 'Otávio']


def avaliacoes_extras():
    """2 a 4 avaliações fictícias por loja, sempre as mesmas (sorteio com semente fixa)."""
    sorte = random.Random(2026)
    saida = {}
    for loja in LOJAS_EXTRAS:
        n = sorte.randint(1, 4)
        textos = sorte.sample(_COMENTARIOS[loja['categoria']], k=min(n, len(_COMENTARIOS[loja['categoria']])))
        saida[loja['usuario']] = [(sorte.choice(_NOMES), sorte.choice([5, 5, 5, 4, 4, 3]), t) for t in textos]
    return saida


# telefones fictícios na sequência dos de demonstração (5582900000010 em diante)
for i, loja in enumerate(LOJAS_EXTRAS, start=10):
    loja['whatsapp'] = f'55829000000{i:02d}'

# cada loja nova tem foto de capa própria e cada produto a sua foto (nenhuma se repete; ver fotos/extras/)
for loja in LOJAS_EXTRAS:
    loja['foto'] = f"vitrine/fotos/extras/{loja['usuario']}-capa.jpg"
    loja['produtos'] = [p[:5] + (f"vitrine/fotos/extras/{loja['usuario']}-{i}.jpg",) for i, p in enumerate(loja['produtos'], 1)]
