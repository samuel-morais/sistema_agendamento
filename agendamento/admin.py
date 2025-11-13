from django.contrib import admin
from .models import (
    Paciente, Medico, Especialidade,
    Consulta, Prontuario, Exame, Convenio
)


# CONVÊNIOS

@admin.register(Convenio)
class ConvenioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'codigo', 'ativo')
    search_fields = ('nome', 'codigo')
    list_filter = ('ativo',)
    list_editable = ('ativo',)


# PACIENTES

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf', 'telefone', 'email', 'data_nascimento', 'criado_em', 'atualizado_em')
    search_fields = ('nome', 'cpf', 'email')
    list_filter = ('data_nascimento', 'criado_em', 'atualizado_em')



# ESPECIALIDADES

@admin.register(Especialidade)
class EspecialidadeAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)


# MÉDICOS

@admin.register(Medico)
class MedicoAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'crm', 'especialidade', 'hora_inicio', 'hora_fim')
    search_fields = ('user__first_name', 'user__last_name', 'crm', 'especialidade__nome')
    list_filter = ('especialidade',)

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Nome Completo'


# CONSULTAS

@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = (
        'paciente', 'medico', 'formatted_data_hora', 'duracao_minutos',
        'status', 'confirmada', 'usa_convenio', 'get_convenio',
        'criado_em', 'atualizado_em'
    )
    search_fields = (
        'paciente__nome',
        'medico__user__first_name',
        'medico__user__last_name',
        'convenio__nome'
    )
    list_filter = (
        'status',
        'medico',
        'confirmada',
        'usa_convenio',
        'convenio',
        'data_hora',
        'criado_em',
        'atualizado_em'
    )

    def formatted_data_hora(self, obj):
        return obj.data_hora.strftime("%d/%m/%Y %H:%M")
    formatted_data_hora.admin_order_field = 'data_hora'
    formatted_data_hora.short_description = 'Data/Hora'

    def get_convenio(self, obj):
        return obj.convenio.nome if obj.convenio else "—"
    get_convenio.short_description = "Convênio"



# PRONTUÁRIOS

@admin.register(Prontuario)
class ProntuarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'paciente', 'criado_em', 'atualizado_em')
    search_fields = ('paciente__nome',)
    list_filter = ('criado_em', 'atualizado_em')



# EXAMES

@admin.register(Exame)
class ExameAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'prontuario', 'observado_por', 'criado_em', 'atualizado_em')
    search_fields = ('nome', 'prontuario__paciente__nome', 'observado_por__username')
    list_filter = ('criado_em', 'atualizado_em')
