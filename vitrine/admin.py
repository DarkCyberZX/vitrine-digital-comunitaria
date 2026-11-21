from django.contrib import admin

from .models import Avaliacao, Banca, Produto, Venda


class ProdutoInline(admin.TabularInline):
    model = Produto
    extra = 0
    fields = ('nome', 'tamanho', 'preco', 'disponibilidade', 'emoji', 'cadastrado_por_voz')


@admin.register(Banca)
class BancaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'responsavel', 'categoria', 'bairro', 'aberta', 'qtd_produtos')
    list_filter = ('categoria', 'bairro', 'aberta')
    search_fields = ('nome', 'responsavel', 'bairro', 'ponto')
    inlines = [ProdutoInline]

    @admin.display(description='produtos')
    def qtd_produtos(self, obj):
        return obj.produtos.count()


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'banca', 'preco', 'disponibilidade', 'cadastrado_por_voz', 'criado_em')
    list_filter = ('disponibilidade', 'cadastrado_por_voz', 'banca__categoria')
    search_fields = ('nome', 'banca__nome')


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ('banca', 'conferiu_no_banco', 'registrada_em')
    list_filter = ('conferiu_no_banco',)


admin.site.site_header = 'Vitrine Digital Comunitária – Administração'
admin.site.site_title = 'Vitrine Digital'
admin.site.index_title = 'Gestão da plataforma'


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ('banca', 'nota', 'nome', 'visivel', 'criada_em')
    list_filter = ('nota', 'visivel', 'banca')
    list_editable = ('visivel',)
    search_fields = ('nome', 'comentario', 'banca__nome')
