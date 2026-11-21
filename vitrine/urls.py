from django.urls import path

from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('banca/<int:pk>/', views.banca, name='banca'),
    path('sobre/', views.sobre, name='sobre'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('painel/', views.painel, name='painel'),
    path('vender/cadastro/', views.cadastro_loja, name='cadastro_loja'),
    path('painel/minha-loja/', views.editar_loja, name='editar_loja'),
    path('painel/produto/<int:pk>/remover/', views.remover_produto, name='remover_produto'),
]
