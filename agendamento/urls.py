from django.urls import path
from . import views

urlpatterns = [
    path('', views.pagina_inicial, name='pagina_inicial'),

    # Consultas
    path('consultas/', views.listar_consultas, name='listar_consultas'),
    path('consultas/novo/', views.criar_consulta, name='criar_consulta'),
    path('consultas/editar/<int:pk>/', views.editar_consulta, name='editar_consulta'),
    path('consultas/excluir/<int:pk>/', views.excluir_consulta, name='excluir_consulta'),

    # Pacientes
    path('pacientes/', views.listar_pacientes, name='listar_pacientes'),
    path('pacientes/novo/', views.criar_paciente, name='criar_paciente'),
    path('pacientes/editar/<int:pk>/', views.editar_paciente, name='editar_paciente'),
    path('pacientes/excluir/<int:pk>/', views.excluir_paciente, name='excluir_paciente'),

    # Médicos
    path('medicos/', views.listar_medicos, name='listar_medicos'),
    path('medicos/novo/', views.criar_medico, name='criar_medico'),
    path('medicos/editar/<int:pk>/', views.editar_medico, name='editar_medico'),
    path('medicos/excluir/<int:pk>/', views.excluir_medico, name='excluir_medico'),
]
