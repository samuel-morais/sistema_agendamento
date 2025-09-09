from django.contrib import admin
from .models import Especialidade, Medico, Paciente, Consulta

# Especialidades
@admin.register(Especialidade)
class EspecialidadeAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

# Médicos

@admin.register(Medico)
class MedicoAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'crm', 'especialidade')
    search_fields = ('user__first_name', 'user__last_name', 'crm')

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Nome'


# Pacientes

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf', 'telefone', 'email', 'data_nascimento')
    search_fields = ('nome', 'cpf')

# Consultas

@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ('formatted_data_hora', 'medico', 'paciente', 'get_status_display')
    list_filter = ('status', 'medico')
    search_fields = ('paciente__nome', 'medico__user__first_name')

    def formatted_data_hora(self, obj):
        return obj.data_hora.strftime("%d/%m/%Y %H:%M")
    formatted_data_hora.admin_order_field = 'data_hora'
    formatted_data_hora.short_description = 'Data/Hora'
