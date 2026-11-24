from django.db import migrations, models

# antes: uma opção pronta ('seg_sab'); agora: cada dia marcado ('seg,ter,qua,qui,sex,sab')
ANTIGO_PARA_NOVO = {
    'todos': 'seg,ter,qua,qui,sex,sab,dom',
    'seg_sex': 'seg,ter,qua,qui,sex',
    'seg_sab': 'seg,ter,qua,qui,sex,sab',
    'fds': 'sab,dom',
}


def converte(apps, schema_editor):
    Banca = apps.get_model('vitrine', 'Banca')
    for antigo, novo in ANTIGO_PARA_NOVO.items():
        Banca.objects.filter(dias=antigo).update(dias=novo)


def desfaz(apps, schema_editor):
    Banca = apps.get_model('vitrine', 'Banca')
    for antigo, novo in ANTIGO_PARA_NOVO.items():
        Banca.objects.filter(dias=novo).update(dias=antigo)


class Migration(migrations.Migration):
    dependencies = [('vitrine', '0011_horario_funcionamento')]
    operations = [
        migrations.AlterField(model_name='banca', name='dias',
                              field=models.CharField(blank=True, max_length=30, verbose_name='dias que abre')),
        migrations.RunPython(converte, desfaz),
    ]
