# Vitrine Digital Comunitária

Protótipo de uma **Tecnologia Social** para dar visibilidade na internet a feirantes, artesãos e pequenos comerciantes de Maceió (AL).
O comerciante cadastra a loja e os produtos (pode ser falando no microfone), e o comprador do bairro encontra as lojas no mapa,
vê preço e disponibilidade antes de sair de casa e combina direto pelo WhatsApp, sem taxa e sem intermediário.

Trabalho da disciplina **Tecnologias Sociais e Assistivas** (Bacharelado em Sistemas de Informação, IFAL, Campus Maceió, 2026).

**Site no ar:** https://victhor.pythonanywhere.com

> As lojas, os produtos, as avaliações e os telefones do site são fictícios, criados só para demonstração.

## O que o protótipo faz

**Para quem compra**
- Busca por loja, produto ou bairro, com filtros de categoria, preço, nota e distância.
- Mapa das lojas (agrupadas quando estão próximas); com a localização permitida, mostra a distância em km e limita o raio.
- Página da loja com produtos (foto, descrição, preço, pronta entrega ou encomenda), a história de quem faz e as avaliações.
- Botão do WhatsApp com mensagem pronta e "Como chegar" pelo Google Maps.

**Para quem vende**
- Cadastro da loja com CEP (o endereço se completa sozinho) e marcação no mapa ou pelo GPS.
- Cadastro de produto **por voz**: fala "tapioca de queijo, oito reais" e o nome e o preço se preenchem.
- Aviso para conferir o Pix no banco antes de entregar.

**Acessibilidade (WCAG 2.2 AA)**
- Ouvir a tela e ouvir os produtos e preços em voz alta, com a voz mais natural do aparelho (dá para trocar).
- Letra grande, alto contraste e uso completo pelo teclado.
- Verificado com axe-core (0 violações) e conferência manual (teclado, zoom 200%, tela de 320 px, alvos de toque).

## Tecnologias

| Parte | Ferramenta |
|---|---|
| Servidor e páginas | Python 3 e Django 5.2 |
| Banco de dados | SQLite |
| Mapa | Leaflet, Leaflet.markercluster e OpenStreetMap |
| Endereço pelo CEP | ViaCEP e Nominatim |
| Voz (falar e ouvir) | Web Speech API, do próprio navegador |
| Hospedagem | PythonAnywhere (plano gratuito) |

## Como rodar no computador

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py popular_demo
python manage.py runserver
```

Abra http://127.0.0.1:8000. Use o Chrome ou o Edge, porque o cadastro por voz usa o reconhecimento de fala do navegador.

### Contas de demonstração

O comando `popular_demo` cria 37 lojas fictícias, os comerciantes (`cida`, `ze`, `lucia`, `rafa`, `nena`, `marcos`, `graca` e outros),
uma conta de cliente (`cliente`) e o administrador (`admin`).

**As senhas não ficam no código.** Defina-as antes de rodar o comando:

```bash
export VITRINE_SENHA_DEMO="escolha-uma-senha"
export VITRINE_SENHA_ADMIN="escolha-outra-senha"
```

Sem essas variáveis, o comando sorteia senhas e mostra no terminal.

## Testes

```bash
python manage.py test vitrine
```

São 41 testes automáticos: login e permissões (um comerciante não mexe na loja de outro), cadastro da loja, envio de fotos,
avaliações, recuperação de senha e o link "Como chegar".

## Publicar

Defina no servidor as variáveis `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0` e `DJANGO_ALLOWED_HOSTS`, além das senhas acima.
Depois rode `migrate`, `popular_demo` e `collectstatic --noinput --clear`.

## Autores

- João Victhor Monteiro Barros
- Roberto dos Santos Silva Junior

Orientação: Profª Mônica Ximenes (IFAL).
