from django.contrib import admin

from apps.core.forms import TarefaForm
from apps.core.models import Gincana, Setor, Tarefa


@admin.register(Gincana)
class GincanaAdmin(admin.ModelAdmin):
    form = TarefaForm

    list_display = ('nome', 'data_inicio', 'data_fim', 'grupo_whatsapp')
    search_fields = ('nome', 'grupo_whatsapp')
    list_filter = ('data_inicio', 'data_fim')


@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    ...


@admin.register(Tarefa)
class TarefaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'gincana', 'setor', 'disponivel_em', 'responsavel')
    search_fields = ('titulo', 'gincana__nome', 'setor__nome', 'responsavel__username')
    list_filter = ('gincana', 'setor', 'disponivel_em')
