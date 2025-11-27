from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [

    # ===========================================================
    # PÁGINA INICIAL
    # ===========================================================
    path('', views.pagina_inicial, name='pagina_inicial'),

    # ===========================================================
    # AUTENTICAÇÃO E PERFIL
    # ===========================================================
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html'
    ), name='login'),

    path('logout/', auth_views.LogoutView.as_view(
        next_page='login'
    ), name='logout'),

    path('cadastrar/', views.cadastrar_usuario, name='cadastrar_usuario'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),

    # AJAX validação
    path("validar/username/", views.validar_username, name="validar_username"),
    path("validar/email/", views.validar_email, name="validar_email"),


    # ===========================================================
    # PACIENTES
    # ===========================================================
    path('pacientes/', views.listar_pacientes, name='listar_pacientes'),
    path('pacientes/novo/', views.criar_paciente, name='criar_paciente'),
    path('pacientes/<int:pk>/editar/', views.editar_paciente, name='editar_paciente'),
    path('pacientes/<int:pk>/excluir/', views.excluir_paciente, name='excluir_paciente'),
    path('pacientes/<int:paciente_id>/historico/', views.historico_paciente, name='historico_paciente'),


    # ===========================================================
    # MÉDICOS
    # ===========================================================
    path('medicos/', views.listar_medicos, name='listar_medicos'),
    path('medicos/novo/', views.criar_medico, name='criar_medico'),
    path('medicos/<int:pk>/editar/', views.editar_medico, name='editar_medico'),
    path('medicos/<int:pk>/excluir/', views.excluir_medico, name='excluir_medico'),


    # ===========================================================
    # NOTIFICAÇÕES
    # ===========================================================
    path('notificacoes_novas/', views.notificacoes_novas, name='notificacoes_novas'),
    path('notificacoes/count/', views.notificacoes_count, name='notificacoes_count'),
    path('notificacoes/lista/', views.notificacoes_list, name='notificacoes_list'),
    path('notificacoes/', views.listar_notificacoes, name='listar_notificacoes'),
    path('notificacoes/marcar_lida/<int:pk>/', views.notificacoes_marcar_lida, name='notificacoes_marcar_lida'),


    # ===========================================================
    # ESPECIALIDADES
    # ===========================================================
    path('especialidades/', views.listar_especialidades, name='listar_especialidades'),
    path('especialidades/nova/', views.criar_especialidade, name='criar_especialidade'),
    path('especialidades/<int:pk>/editar/', views.editar_especialidade, name='editar_especialidade'),
    path('especialidades/<int:pk>/excluir/', views.excluir_especialidade, name='excluir_especialidade'),


    # ===========================================================
    # CONSULTAS
    # ===========================================================
    path('consultas/', views.listar_consultas, name='listar_consultas'),
    path('consultas/nova/', views.criar_consulta, name='criar_consulta'),
    path('consultas/<int:pk>/editar/', views.editar_consulta, name='editar_consulta'),
    path('consultas/<int:pk>/excluir/', views.excluir_consulta, name='excluir_consulta'),
    path('consultas/<int:pk>/cancelar/', views.cancelar_consulta, name='cancelar_consulta'),
    path('consultas/<int:pk>/confirmar/', views.confirmar_consulta, name='confirmar_consulta'),

    # AJAX consultas
    path("consultas/horarios_disponiveis/", views.horarios_disponiveis, name="horarios_disponiveis"),
    path("consultas/medicos_por_especialidade/", views.medicos_por_especialidade, name="medicos_por_especialidade"),
    path("consultas/medicos_com_disponibilidade/", views.medicos_com_disponibilidade, name="medicos_com_disponibilidade"),


    # ===========================================================
    # PRONTUÁRIOS
    # ===========================================================
    path('prontuarios/', views.listar_prontuarios, name='listar_prontuarios'),

    # Criar
    path("prontuario/criar/<int:paciente_id>/", views.criar_prontuario, name="criar_prontuario"),

    # Detalhes / editar / excluir
    path("prontuario/<int:pk>/", views.prontuario_detalhe, name="prontuario_detalhe"),
    path("prontuario/<int:pk>/editar/", views.editar_prontuario, name="editar_prontuario"),
    path("prontuario/<int:pk>/excluir/", views.excluir_prontuario, name="excluir_prontuario"),

    # PDF + completo
    path("prontuario/pdf/<int:pk>/", views.prontuario_pdf, name="prontuario_pdf"),
    path("prontuario/completo/<int:pk>/", views.prontuario_completo, name="prontuario_completo"),
    path("prontuario/<int:pk>/editar/completo/", views.editar_prontuario_completo, name="editar_prontuario_completo"),


    # ===========================================================
    # EXAMES E DOCUMENTOS
    # ===========================================================
    path("prontuario/documento/<int:doc_id>/excluir/", views.excluir_documento, name="excluir_documento"),
    path("prontuario/exame/<int:exame_id>/excluir/", views.excluir_exame, name="excluir_exame"),

    path('exames/upload/<int:pk>/', views.upload_exame, name='upload_exame'),
    path("exames/anexar/<int:prontuario_id>/", views.anexar_exame, name="anexar_exame"),


    # ===========================================================
    # TROCAR SENHA (PADRÃO DJANGO)
    # ===========================================================
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='registration/password_change_form.html',
        success_url='/perfil/'
    ), name='password_change'),
]
