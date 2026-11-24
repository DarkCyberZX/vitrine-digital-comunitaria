"""Coloca um horário de funcionamento (fictício) nas lojas de demonstração que ainda não têm.

Não mexe em loja que já tem horário. Uso: python manage.py preencher_horarios
"""
from datetime import time

from django.core.management.base import BaseCommand

from vitrine.models import Banca

D = Banca.Dias
# horário típico de cada tipo de loja: (dias, abre, fecha)
POR_CATEGORIA = {
    'comida': [(D.SEG_SAB, time(6), time(13)), (D.TODOS, time(7), time(14)), (D.SEG_SAB, time(15), time(21))],
    'frutas': [(D.SEG_SAB, time(5, 30), time(13)), (D.TODOS, time(6), time(12)), (D.SEG_SAB, time(6), time(14))],
    'artesanato': [(D.SEG_SAB, time(9), time(18)), (D.TODOS, time(9), time(17)), (D.FDS, time(8), time(16))],
    'roupas': [(D.SEG_SAB, time(8), time(18)), (D.SEG_SAB, time(9), time(17)), (D.FDS, time(8), time(15))],
    'servicos': [(D.SEG_SEX, time(8), time(18)), (D.SEG_SAB, time(8), time(17)), (D.SEG_SEX, time(8, 30), time(17, 30))],
}
# lojas cujo nome pede um horário próprio
POR_NOME = {
    'Cuscuz': (D.TODOS, time(5, 30), time(10)),
    'Tapioca': (D.TODOS, time(15), time(21)),
    'Quentinhas': (D.SEG_SAB, time(10, 30), time(14, 30)),
    'Caldo de Cana': (D.TODOS, time(8), time(17)),
    'Coco Gelado': (D.TODOS, time(8), time(17, 30)),
    'Coco do': (D.TODOS, time(8), time(17)),
    'Moda Praia': (D.TODOS, time(9), time(17)),
    'Sururu': (D.FDS, time(10), time(16)),
    'Goma': (D.SEG_SAB, time(5, 30), time(12)),
}


class Command(BaseCommand):
    help = 'Preenche o horário de funcionamento das lojas que ainda não têm.'

    def handle(self, *args, **opts):
        feitas, vistas = 0, {}
        for b in Banca.objects.filter(abre__isnull=True).order_by('nome'):
            escolha = next((h for chave, h in POR_NOME.items() if chave in b.nome), None)
            if escolha is None:
                opcoes = POR_CATEGORIA.get(b.categoria, POR_CATEGORIA['servicos'])
                i = vistas.get(b.categoria, 0); vistas[b.categoria] = i + 1
                escolha = opcoes[i % len(opcoes)]
            b.dias, b.abre, b.fecha = escolha
            b.save(update_fields=['dias', 'abre', 'fecha'])
            feitas += 1
        self.stdout.write(self.style.SUCCESS(f'Horário colocado em {feitas} loja(s).'))
