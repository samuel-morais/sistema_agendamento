# ===============================================================
# IMPORTAÇÕES
# ===============================================================

from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User, Group
from django.db import transaction
from datetime import datetime, time, timedelta
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from xhtml2pdf import pisa
import io

from .models import (
    Consulta, Paciente, Medico, Especialidade,
    Prontuario, Exame, Notificacao, Convenio
)
from .forms import (
    ConsultaForm, CustomUserCreationForm, PacienteForm, MedicoForm,
    EspecialidadeForm, ExameForm
)

# ===============================================================
# PERMISSÕES — FUNÇÕES AUXILIARES
# ===============================================================

def is_medico(user):
    """Retorna True se o usuário é médico."""
    return hasattr(user, 'perfil_medico') and user.perfil_medico is not None


def is_secretaria(user):
    """Superusuário ou staff é tratado como secretaria/admin."""
    return user.is_authenticated and (user.is_superuser or user.is_staff)


def is_usuario_padrao(user):
    """Usuário pertence ao grupo Usuário Padrão."""
    return user.is_authenticated and user.groups.filter(name='Usuário Padrão').exists()


def context_user_flags(request):
    """Flags adicionadas ao contexto para exibição condicional no template."""
    return {
        'is_usuario_padrao': is_usuario_padrao(request.user),
        'is_medico_user': is_medico(request.user)
    }


# ===============================================================
# DASHBOARD — PÁGINA INICIAL
# ===============================================================

@login_required
def pagina_inicial(request):

    user = request.user
    context = {}

    # -----------------------------------------------------------
    # MÉDICO — mostra apenas dados relacionados ao médico logado
    # -----------------------------------------------------------
    if is_medico(user):

        medico = user.perfil_medico

        consultas_qs = (Consulta.objects
                        .filter(medico=medico)
                        .select_related("paciente", "medico__user")
                        .order_by("data_hora"))

        consultas_pendentes = consultas_qs.filter(status='agendada')[:10]
        consultas_confirmadas = consultas_qs.filter(status='confirmada')[:10]
        consultas_canceladas = consultas_qs.filter(status='cancelada')[:10]

        prontuarios = Prontuario.objects.filter(
            paciente__consultas__medico=medico
        ).distinct()

        total_pacientes_medico = Paciente.objects.filter(
            consultas__medico=medico
        ).distinct().count()

        context.update({
            'consultas': consultas_qs,
            'consultas_pendentes': consultas_pendentes,
            'consultas_confirmadas': consultas_confirmadas,
            'consultas_canceladas': consultas_canceladas,

            'total_consultas': consultas_qs.count(),
            'total_prontuarios': prontuarios.count(),
            'total_pacientes_medico': total_pacientes_medico,

            'notificacoes': Notificacao.objects.filter(usuario=user).order_by('-criado_em')[:5],
        })

    # -----------------------------------------------------------
    # PACIENTE — mostra somente conteúdo vinculado ao paciente
    # -----------------------------------------------------------
    elif is_usuario_padrao(user):

        paciente = getattr(user, 'perfil_paciente', None)

        if paciente:
            consultas = Consulta.objects.filter(
                paciente=paciente
            ).select_related("paciente", "medico__user").order_by("data_hora")

            prontuarios = Prontuario.objects.filter(paciente=paciente)
            total_exames = Exame.objects.filter(prontuario__paciente=paciente).count()
        else:
            consultas = Consulta.objects.none()
            prontuarios = Prontuario.objects.none()
            total_exames = 0

        context.update({
            'consultas': consultas,
            'total_consultas': consultas.count(),
            'total_prontuarios': prontuarios.count(),
            'total_exames': total_exames,

            'notificacoes': Notificacao.objects.filter(usuario=user).order_by('-criado_em')[:5],
        })

    # -----------------------------------------------------------
    # ADMIN / SECRETÁRIA — visualiza tudo
    # -----------------------------------------------------------
    else:

        consultas_qs = Consulta.objects.select_related(
            "paciente", "medico__user"
        ).order_by("data_hora")

        consultas_pendentes = consultas_qs.filter(status='agendada')[:10]
        consultas_confirmadas = consultas_qs.filter(status='confirmada')[:10]
        consultas_canceladas = consultas_qs.filter(status='cancelada')[:10]

        context.update({
            'consultas': consultas_qs,

            'total_consultas': consultas_qs.count(),
            'total_pacientes': Paciente.objects.count(),
            'total_medicos': Medico.objects.count(),
            'total_especialidades': Especialidade.objects.count(),
            'total_prontuarios': Prontuario.objects.count(),
            'total_exames': Exame.objects.count(),

            'consultas_pendentes': consultas_pendentes,
            'consultas_confirmadas': consultas_confirmadas,
            'consultas_canceladas': consultas_canceladas,

            'notificacoes': Notificacao.objects.filter(usuario=user).order_by('-criado_em')[:5],
        })

    context.update(context_user_flags(request))
    return render(request, 'agendamento/pagina_inicial.html', context)


# ===============================================================
# PERFIL — PERFIL DO USUÁRIO
# ===============================================================

@login_required
def perfil_usuario(request):
    from .forms import UserPacienteProfileForm

    user = request.user

    if request.method == 'POST':
        form = UserPacienteProfileForm(request.POST, request.FILES, instance=user)

        if form.is_valid():
            form.save()
            messages.success(request, "Perfil atualizado com sucesso!")
            return redirect('perfil_usuario')

        messages.error(request, "Corrija os erros abaixo.")

    else:
        form = UserPacienteProfileForm(instance=user)

    context = {"form": form, "titulo": "Meu Perfil"}
    context.update(context_user_flags(request))

    return render(request, 'agendamento/usuarios/perfil_usuario.html', context)


# ===============================================================
# USUÁRIOS — CADASTRAR NOVO USUÁRIO
# ===============================================================

def cadastrar_usuario(request):
    form = CustomUserCreationForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.save()

            # adiciona automaticamente ao grupo Usuário Padrão
            grupo, _ = Group.objects.get_or_create(name='Usuário Padrão')
            user.groups.add(grupo)

            messages.success(request, "Conta criada com sucesso. Faça login para continuar.")
            return redirect('login')

        messages.error(request, "Corrija os erros abaixo.")

    context = {'form': form}
    context.update(context_user_flags(request))

    return render(request, 'agendamento/cadastrar.html', context)


# ===============================================================
# USUÁRIOS — VALIDAÇÃO AJAX (username / email)
# ===============================================================

def validar_username(request):
    username = request.GET.get("u", "")
    exists = User.objects.filter(username__iexact=username).exists()
    return JsonResponse({"exists": exists})


def validar_email(request):
    email = request.GET.get("e", "")
    exists = User.objects.filter(email__iexact=email).exists()
    return JsonResponse({"exists": exists})

# ===============================================================
# PACIENTES — LISTAR
# ===============================================================

@login_required
def listar_pacientes(request):
    pacientes = Paciente.objects.all().order_by('nome')

    context = {'pacientes': pacientes}
    context.update(context_user_flags(request))

    return render(request, 'agendamento/pacientes/listar_pacientes.html', context)


# ===============================================================
# PACIENTES — CRIAR
# ===============================================================

@login_required
def criar_paciente(request):
    form = PacienteForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Paciente criado com sucesso!')
        return redirect('listar_pacientes')

    context = {
        'form': form,
        'titulo': 'Novo Paciente'
    }
    context.update(context_user_flags(request))

    return render(request, 'agendamento/pacientes/paciente_form.html', context)


# ===============================================================
# PACIENTES — EDITAR
# ===============================================================

@login_required
def editar_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    form = PacienteForm(request.POST or None, instance=paciente)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Paciente atualizado com sucesso!')
        return redirect('listar_pacientes')

    context = {
        'form': form,
        'titulo': 'Editar Paciente'
    }
    context.update(context_user_flags(request))

    return render(request, 'agendamento/pacientes/paciente_form.html', context)


# ===============================================================
# PACIENTES — EXCLUIR
# ===============================================================

@login_required
def excluir_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)

    if request.method == 'POST':
        paciente.delete()
        messages.success(request, 'Paciente excluído com sucesso!')
        return redirect('listar_pacientes')

    context = {'paciente': paciente}
    context.update(context_user_flags(request))

    return render(request, 'agendamento/pacientes/paciente_confirm_delete.html', context)


# ===============================================================
# PACIENTES — HISTÓRICO
# ===============================================================

@login_required
def historico_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, pk=paciente_id)

    consultas = (
        Consulta.objects
        .filter(paciente=paciente)
        .select_related('medico')
        .order_by('-data_hora')
    )

    context = {
        'paciente': paciente,
        'consultas': consultas
    }
    context.update(context_user_flags(request))

    return render(request, 'agendamento/pacientes/historico_paciente.html', context)


# ===============================================================
# MÉDICOS — LISTAR
# ===============================================================

@login_required
@user_passes_test(is_secretaria)
def listar_medicos(request):
    medicos = (
        Medico.objects
        .select_related('user', 'especialidade')
        .all()
        .order_by('user__first_name')
    )

    context = {'medicos': medicos}
    context.update(context_user_flags(request))

    return render(request, 'agendamento/medicos/listar_medicos.html', context)


# ===============================================================
# MÉDICOS — CRIAR
# ===============================================================

@login_required
@user_passes_test(is_secretaria)
def criar_medico(request):
    form = MedicoForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Médico cadastrado com sucesso!')
        return redirect('listar_medicos')

    context = {
        'form': form,
        'titulo': 'Novo Médico'
    }
    context.update(context_user_flags(request))

    return render(request, 'agendamento/medicos/medico_form.html', context)


# ===============================================================
# MÉDICOS — EDITAR
# ===============================================================

@login_required
@user_passes_test(is_secretaria)
def editar_medico(request, pk):
    medico = get_object_or_404(Medico, pk=pk)
    form = MedicoForm(request.POST or None, instance=medico)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Médico atualizado com sucesso!')
        return redirect('listar_medicos')

    context = {
        'form': form,
        'titulo': 'Editar Médico'
    }
    context.update(context_user_flags(request))

    return render(request, 'agendamento/medicos/medico_form.html', context)


# ===============================================================
# MÉDICOS — EXCLUIR
# ===============================================================

@login_required
@user_passes_test(is_secretaria)
def excluir_medico(request, pk):
    medico = get_object_or_404(Medico, pk=pk)

    if request.method == 'POST':
        medico.delete()
        messages.success(request, 'Médico excluído com sucesso!')
        return redirect('listar_medicos')

    context = {'medico': medico}
    context.update(context_user_flags(request))

    return render(request, 'agendamento/medicos/medico_confirm_delete.html', context)


# ===============================================================
# ESPECIALIDADES — LISTAR
# ===============================================================

@login_required
@user_passes_test(is_secretaria)
def listar_especialidades(request):
    especialidades = Especialidade.objects.all().order_by('nome')

    context = {'especialidades': especialidades}
    context.update(context_user_flags(request))

    return render(request, 'agendamento/especialidades/listar_especialidades.html', context)


# ===============================================================
# ESPECIALIDADES — CRIAR
# ===============================================================

@login_required
@user_passes_test(is_secretaria)
def criar_especialidade(request):
    form = EspecialidadeForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Especialidade cadastrada com sucesso!')
        return redirect('listar_especialidades')

    context = {
        'form': form,
        'titulo': 'Nova Especialidade'
    }
    context.update(context_user_flags(request))

    return render(request, 'agendamento/especialidades/especialidade_form.html', context)


# ===============================================================
# ESPECIALIDADES — EDITAR
# ===============================================================

@login_required
@user_passes_test(is_secretaria)
def editar_especialidade(request, pk):
    especialidade = get_object_or_404(Especialidade, pk=pk)
    form = EspecialidadeForm(request.POST or None, instance=especialidade)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Especialidade atualizada com sucesso!')
        return redirect('listar_especialidades')

    context = {
        'form': form,
        'titulo': 'Editar Especialidade'
    }
    context.update(context_user_flags(request))

    return render(request, 'agendamento/especialidades/especialidade_form.html', context)


# ===============================================================
# ESPECIALIDADES — EXCLUIR
# ===============================================================

@login_required
@user_passes_test(is_secretaria)
def excluir_especialidade(request, pk):
    especialidade = get_object_or_404(Especialidade, pk=pk)

    if request.method == 'POST':
        especialidade.delete()
        messages.success(request, 'Especialidade excluída com sucesso!')
        return redirect('listar_especialidades')

    context = {
        'especialidade': especialidade,
        'titulo': 'Excluir Especialidade'
    }
    context.update(context_user_flags(request))

    return render(request, 'agendamento/especialidades/especialidade_confirm_delete.html', context)


# ===============================================================
# CONSULTAS — LISTAR
# ===============================================================

@login_required
def listar_consultas(request):
    user = request.user
    context = {}

    # Paciente — visualiza somente as suas consultas
    if is_usuario_padrao(user):
        paciente = getattr(user, 'perfil_paciente', None)

        if paciente:
            consultas = Consulta.objects.filter(paciente=paciente).order_by('-data_hora')
        else:
            consultas = Consulta.objects.none()

    # Médico — visualiza apenas as consultas dele
    elif is_medico(user):
        medico = user.perfil_medico

        consultas = (
            Consulta.objects
            .filter(medico=medico)
            .select_related("paciente", "medico__user")
            .order_by('-data_hora')
        )

        # marca notificações como lidas ao abrir
        Notificacao.objects.filter(usuario=user, lida=False).update(lida=True)

    # Admin / Secretaria — visualiza tudo
    else:
        consultas = Consulta.objects.all().order_by('-data_hora')

    # bloqueio de horários futuros
    for c in consultas:
        c.horario_bloqueado = (
            c.status == 'agendada' and
            c.data_hora > timezone.now()
        )

    context.update({
        'consultas': consultas,
        'notificacoes': Notificacao.objects.filter(usuario=user).order_by('-criado_em')[:5],
    })
    context.update(context_user_flags(request))

    return render(request, 'agendamento/consultas/listar_consultas.html', context)


# ===============================================================
# CONSULTAS — CRIAR
# ===============================================================

@login_required
def criar_consulta(request):
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        form = ConsultaForm(request.POST, user=request.user)

        data = request.POST.get('data')
        hora = request.POST.get('hora')

        # monta datetime
        try:
            data_hora = datetime.strptime(f"{data} {hora}", "%Y-%m-%d %H:%M") if data and hora else None
        except:
            data_hora = None

        if form.is_valid() and data_hora:
            try:
                medico = form.cleaned_data['medico']
                duracao = form.cleaned_data.get('duracao_minutos', 30)

                usa_convenio = request.POST.get('usa_convenio') == 'on'
                convenio_id = request.POST.get('convenio')

                convenio_obj = None
                if convenio_id:
                    try:
                        convenio_obj = Convenio.objects.get(id=convenio_id)
                    except Convenio.DoesNotExist:
                        convenio_obj = None

                with transaction.atomic():

                    # verifica conflito de horário
                    conflito = Consulta.objects.filter(
                        medico=medico,
                        data_hora=timezone.make_aware(data_hora)
                    ).exists()

                    if conflito:
                        msg = "Este horário já está reservado. Escolha outro horário."

                        if is_ajax:
                            return JsonResponse({"ok": False, "errors": {"hora": [msg]}}, status=400)

                        messages.error(request, msg)
                        return redirect('criar_consulta')

                    paciente_vinculado = get_paciente_do_usuario(request.user)

                    consulta = form.save(commit=False)
                    consulta.paciente = paciente_vinculado
                    consulta.usuario = request.user
                    consulta.data_hora = timezone.make_aware(data_hora)
                    consulta.status = 'agendada'
                    consulta.confirmada = False
                    consulta.usa_convenio = bool(usa_convenio)
                    consulta.convenio = convenio_obj if usa_convenio else None
                    consulta.save()

                    # notifica o médico
                    Notificacao.objects.create(
                        usuario=medico.user,
                        titulo="Nova consulta agendada",
                        mensagem=(
                            f"Paciente {consulta.paciente.nome} agendou uma consulta "
                            f"para {consulta.data_hora.strftime('%d/%m/%Y')} às "
                            f"{consulta.data_hora.strftime('%H:%M')}."
                        ),
                        link=reverse('pagina_inicial')
                    )

                if is_ajax:
                    return JsonResponse({
                        "ok": True,
                        "consulta": {
                            "id": consulta.id,
                            "paciente": consulta.paciente.nome,
                            "medico": str(consulta.medico),
                            "data": consulta.data_hora.strftime("%d/%m/%Y"),
                            "hora": consulta.data_hora.strftime("%H:%M"),
                            "convenio": consulta.convenio.nome if consulta.usa_convenio and consulta.convenio else None
                        }
                    })

                messages.success(request, "Consulta criada com sucesso!")
                return redirect('listar_consultas')

            except Exception as e:
                if is_ajax:
                    return JsonResponse({"ok": False, "errors": {"__all__": [str(e)]}}, status=500)

                messages.error(request, f"Erro inesperado: {e}")

        if is_ajax:
            errors = form.errors.get_json_data()
            simplified = {
                field: [e['message'] for e in err]
                for field, err in errors.items()
            }
            return JsonResponse({"ok": False, "errors": simplified}, status=400)

        messages.error(request, "Erro ao salvar consulta. Verifique os campos.")

    else:
        form = ConsultaForm(user=request.user)

    especialidades = Especialidade.objects.all().order_by('nome')
    convenios = Convenio.objects.filter(ativo=True).order_by('nome')

    context = {
        'form': form,
        'titulo': 'Nova Consulta',
        'especialidades': especialidades,
        'convenios': convenios,
    }
    context.update(context_user_flags(request))

    return render(request, 'agendamento/consultas/consulta_form.html', context)

# ===============================================================
# CONSULTAS — CONFIRMAR
# ===============================================================

@login_required
def confirmar_consulta(request, pk):
    if request.method != 'POST':
        return redirect('listar_consultas')

    consulta = get_object_or_404(Consulta, pk=pk)

    # Permissão — Médico responsável, secretaria ou admin
    if not (
        (is_medico(request.user) and consulta.medico.user == request.user)
        or request.user.is_staff
        or request.user.is_superuser
    ):
        messages.error(request, "Você não tem permissão para confirmar esta consulta.")
        return redirect('listar_consultas')

    consulta.status = 'confirmada'
    consulta.confirmada = True
    consulta.save()

    # Notifica o paciente
    if consulta.paciente and consulta.paciente.usuario:
        Notificacao.objects.create(
            usuario=consulta.paciente.usuario,
            titulo="Consulta Confirmada",
            mensagem=(
                f"Sua consulta com o médico {consulta.medico.user.get_full_name()} foi confirmada para "
                f"{timezone.localtime(consulta.data_hora).strftime('%d/%m/%Y %H:%M')}."
            ),
            link=reverse('pagina_inicial')
        )

    messages.success(request, "Consulta confirmada com sucesso!")
    return redirect('pagina_inicial')


# ===============================================================
# CONSULTAS — FUNÇÃO AUXILIAR (GARANTE UM PACIENTE)
# ===============================================================

def get_paciente_do_usuario(user):
    if hasattr(user, 'perfil_paciente'):
        return user.perfil_paciente

    paciente, _ = Paciente.objects.get_or_create(
        usuario=user,
        defaults={
            'nome': user.get_full_name() or user.username,
            'email': user.email
        }
    )
    return paciente


# ===============================================================
# CONSULTAS — EDITAR
# ===============================================================

@login_required
def editar_consulta(request, pk):
    consulta = get_object_or_404(Consulta, pk=pk)

    # Permissão
    if not (
        is_secretaria(request.user)
        or is_medico(request.user)
        or consulta.paciente == getattr(request.user, 'perfil_paciente', None)
    ):
        messages.error(request, 'Você não tem permissão para editar esta consulta.')
        return redirect('listar_consultas')

    if request.method == 'POST':
        form = ConsultaForm(request.POST, instance=consulta, user=request.user)

        if form.is_valid():
            data = form.cleaned_data['data']
            hora = form.cleaned_data['hora']
            duracao = form.cleaned_data.get('duracao_minutos') or consulta.duracao_minutos

            data_hora = timezone.make_aware(
                datetime.combine(data, hora),
                timezone.get_current_timezone()
            )

            consulta.data_hora = data_hora
            consulta.medico = form.cleaned_data['medico']
            consulta.observacoes = form.cleaned_data['observacoes']
            consulta.status = form.cleaned_data['status']
            consulta.confirmada = form.cleaned_data['confirmada']
            consulta.duracao_minutos = duracao

            if 'usa_convenio' in form.cleaned_data:
                consulta.usa_convenio = form.cleaned_data['usa_convenio']

            if 'convenio' in form.cleaned_data:
                consulta.convenio = form.cleaned_data['convenio']

            consulta.save()

            messages.success(request, 'Consulta atualizada com sucesso!')
            return redirect('listar_consultas')

        messages.error(request, 'Corrija os erros do formulário.')

    else:
        inicial = {
            'data': consulta.data_hora.date(),
            'hora': consulta.data_hora.time().strftime('%H:%M'),
            'duracao_minutos': consulta.duracao_minutos,
        }

        form = ConsultaForm(
            instance=consulta,
            initial=inicial,
            user=request.user
        )

    context = {
        'form': form,
        'titulo': 'Editar Consulta',
        'consulta': consulta
    }
    context.update(context_user_flags(request))

    return render(request, 'agendamento/consultas/consulta_form.html', context)


# ===============================================================
# CONSULTAS — EXCLUIR
# ===============================================================

@login_required
def excluir_consulta(request, pk):
    consulta = get_object_or_404(Consulta, pk=pk)

    # Permissões: médico, secretaria, admin ou paciente dono
    if not (
        is_secretaria(request.user)
        or is_medico(request.user)
        or consulta.paciente == getattr(request.user, 'perfil_paciente', None)
    ):
        messages.error(request, 'Você não tem permissão para excluir esta consulta.')
        return redirect('listar_consultas')

    if request.method == 'POST':
        consulta.delete()
        messages.success(request, 'Consulta excluída com sucesso!')
        return redirect('listar_consultas')

    context = {'consulta': consulta, 'titulo': 'Excluir Consulta'}
    context.update(context_user_flags(request))

    return render(request, 'agendamento/consultas/consulta_confirm_delete.html', context)


# ===============================================================
# CONSULTAS — CANCELAR
# ===============================================================

@login_required
def cancelar_consulta(request, pk):
    consulta = get_object_or_404(Consulta, pk=pk)

    # Permissões
    if not (
        is_secretaria(request.user)
        or is_medico(request.user)
        or consulta.paciente == getattr(request.user, 'perfil_paciente', None)
    ):
        messages.error(request, 'Você não tem permissão para cancelar esta consulta.')
        return redirect('listar_consultas')

    if request.method == 'POST':
        consulta.status = 'cancelada'
        consulta.save()

        # Notifica o paciente
        if consulta.paciente and consulta.paciente.usuario:
            Notificacao.objects.create(
                usuario=consulta.paciente.usuario,
                titulo="Consulta Cancelada",
                mensagem=(
                    f"A consulta com {consulta.medico.user.get_full_name()} "
                    f"em {consulta.data_hora.strftime('%d/%m/%Y %H:%M')} foi cancelada."
                ),
                link=reverse('pagina_inicial')
            )

        messages.success(request, 'Consulta cancelada com sucesso.')
        return redirect('listar_consultas')


# ===============================================================
# CONSULTAS — HORÁRIOS DISPONÍVEIS (AJAX)
# ===============================================================

def horarios_disponiveis(request):
    medico_id = request.GET.get("medico_id")
    data_str = request.GET.get("data")

    if not medico_id or not data_str:
        return JsonResponse({"horarios": []}, status=400)

    try:
        data_consulta = datetime.strptime(data_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"horarios": []}, status=400)

    try:
        medico = Medico.objects.get(id=medico_id)
        hora_inicio = medico.hora_inicio or time(8, 0)
        hora_fim = medico.hora_fim or time(17, 0)
    except:
        return JsonResponse({"horarios": []}, status=404)

    intervalo = timedelta(minutes=30)

    consultas = Consulta.objects.filter(
        medico_id=medico_id,
        data_hora__date=data_consulta,
        status__in=["agendada", "confirmada"]
    )

    horarios_ocupados = {
        timezone.localtime(c.data_hora).strftime("%H:%M")
        for c in consultas
    }

    disponiveis = []
    atual = datetime.combine(data_consulta, hora_inicio)
    fim = datetime.combine(data_consulta, hora_fim)

    while atual < fim:
        hora_str = atual.strftime("%H:%M")
        if hora_str not in horarios_ocupados:
            disponiveis.append(hora_str)
        atual += intervalo

    return JsonResponse({"horarios": disponiveis})


# ===============================================================
# MÉDICOS — LISTAR POR ESPECIALIDADE (AJAX)
# ===============================================================

def medicos_por_especialidade(request):
    especialidade_id = request.GET.get("especialidade_id")

    if not especialidade_id:
        return JsonResponse({"medicos": []})

    medicos = (
        Medico.objects
        .filter(especialidade_id=especialidade_id)
        .select_related("especialidade", "user")
        .order_by("user__first_name")
    )

    data = [
        {
            "id": m.id,
            "nome": m.user.get_full_name() or m.user.username,
            "especialidade": m.especialidade.nome
        }
        for m in medicos
    ]

    return JsonResponse({"medicos": data})


# ===============================================================
# MÉDICOS — COM DISPONIBILIDADE (AJAX)
# ===============================================================

def medicos_com_disponibilidade(request):
    data_str = request.GET.get("data")
    especialidade = request.GET.get("especialidade")

    if not data_str:
        return JsonResponse({"medicos": []})

    try:
        data_consulta = datetime.strptime(data_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"medicos": []})

    medicos_qs = Medico.objects.select_related("user", "especialidade")

    if especialidade:
        medicos_qs = medicos_qs.filter(especialidade_id=especialidade)

    medicos_disponiveis = []

    for medico in medicos_qs:
        consultas_agendadas = Consulta.objects.filter(
            medico=medico,
            data_hora__date=data_consulta,
            status__in=["agendada", "confirmada"]
        ).count()

        if consultas_agendadas < 18:  # limite diário
            medicos_disponiveis.append({
                "id": medico.id,
                "nome": medico.user.get_full_name(),
                "especialidade": medico.especialidade.nome
            })

    return JsonResponse({"medicos": medicos_disponiveis})

# ===============================================================
# NOTIFICAÇÕES — NOVAS (NÃO LIDAS)
# ===============================================================

@login_required
def notificacoes_novas(request):
    novas = (
        Notificacao.objects
        .filter(usuario=request.user, lida=False)
        .order_by('-criado_em')
    )

    data = [{
        'id': n.id,
        'titulo': n.titulo,
        'mensagem': n.mensagem,
        'link': n.link,
        'criado_em': timezone.localtime(n.criado_em).strftime('%d/%m/%Y %H:%M'),
    } for n in novas]

    return JsonResponse({'novas': data})


# ===============================================================
# NOTIFICAÇÕES — CONTAGEM
# ===============================================================

@login_required
def notificacoes_count(request):
    count = Notificacao.objects.filter(
        usuario=request.user,
        lida=False
    ).count()

    return JsonResponse({'count': count})


# ===============================================================
# NOTIFICAÇÕES — DROPDOWN LIST
# ===============================================================

@login_required
def notificacoes_list(request):
    limit = int(request.GET.get('limit', 8))

    notificacoes = (
        Notificacao.objects
        .filter(usuario=request.user)
        .order_by('-criado_em')[:limit]
    )

    data = [
        {
            'id': n.id,
            'titulo': n.titulo,
            'mensagem': n.mensagem,
            'link': n.link or '',
            'lida': n.lida,
            'criado_em': timezone.localtime(n.criado_em).strftime('%d/%m/%Y %H:%M'),
        }
        for n in notificacoes
    ]

    return JsonResponse({'notificacoes': data})


# ===============================================================
# NOTIFICAÇÕES — LISTAR PÁGINA COMPLETA
# ===============================================================

@login_required
def listar_notificacoes(request):
    f = request.GET.get('f', 'all')

    qs = Notificacao.objects.filter(usuario=request.user).order_by('-criado_em')

    if f == 'unread':
        qs = qs.filter(lida=False)
    elif f == 'read':
        qs = qs.filter(lida=True)

    context = {'notificacoes': qs}
    context.update(context_user_flags(request))

    return render(request, 'agendamento/notificacoes/listar_notificacoes.html', context)


# ===============================================================
# NOTIFICAÇÕES — MARCAR COMO LIDA
# ===============================================================

@login_required
@require_POST
def notificacoes_marcar_lida(request, pk):
    try:
        n = Notificacao.objects.get(pk=pk, usuario=request.user)
    except Notificacao.DoesNotExist:
        return JsonResponse(
            {'ok': False, 'error': 'Notificação não encontrada'},
            status=404
        )

    n.lida = True
    n.save(update_fields=['lida'])

    return JsonResponse({'ok': True})


# ===============================================================
# PRONTUÁRIO — CRIAR
# ===============================================================

@login_required
def criar_prontuario(request, paciente_id):
    paciente = get_object_or_404(Paciente, pk=paciente_id)

    if request.method == "POST":
        descricao = request.POST.get("descricao")
        queixa = request.POST.get("queixa")
        diagnostico = request.POST.get("diagnostico")
        cid = request.POST.get("cid")
        medicacao = request.POST.get("medicacao")
        anexo = request.FILES.get("anexo")

        prontuario = Prontuario.objects.create(
            paciente=paciente,
            descricao=descricao,
            queixa=queixa,
            diagnostico=diagnostico,
            cid=cid,
            medicacao=medicacao,
            anexo=anexo
        )

        messages.success(request, "Prontuário criado com sucesso!")
        return redirect("prontuario_detalhe", prontuario.pk)

    return render(request, "agendamento/prontuarios/prontuario_form.html", {
        "paciente": paciente,
        "titulo": "Novo Prontuário",
        "prontuario": None,
    })


# ===============================================================
# PRONTUÁRIO — GERAR PDF
# ===============================================================

@login_required
def prontuario_pdf(request, pk):
    prontuario = get_object_or_404(Prontuario, pk=pk)

    exames = Exame.objects.filter(prontuario=prontuario)
    consultas = Consulta.objects.filter(paciente=prontuario.paciente)

    html = render_to_string(
        "agendamento/prontuarios/prontuario_pdf.html",
        {
            "prontuario": prontuario,
            "paciente": prontuario.paciente,
            "exames": exames,
            "consultas": consultas
        }
    )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename=\"prontuario_{pk}.pdf\"'

    pisa.CreatePDF(io.BytesIO(html.encode("utf-8")), dest=response)

    return response


# ===============================================================
# PRONTUÁRIO — COMPLETO
# ===============================================================

@login_required
def prontuario_completo(request, pk):
    prontuario = get_object_or_404(Prontuario, pk=pk)
    paciente = prontuario.paciente

    consultas = Consulta.objects.filter(paciente=paciente).order_by("-data_hora")
    exames = Exame.objects.filter(prontuario=prontuario).order_by("-criado_em")

    context = {
        "prontuario": prontuario,
        "paciente": paciente,
        "consultas": consultas,
        "exames": exames
    }
    context.update(context_user_flags(request))

    return render(request, "agendamento/prontuarios/prontuario_completo.html", context)


# ===============================================================
# PRONTUÁRIOS — LISTAR
# ===============================================================

@login_required
def listar_prontuarios(request):
    user = request.user

    # Paciente — vê apenas dele
    if is_usuario_padrao(user):
        paciente = getattr(user, "perfil_paciente", None)

        prontuarios = Prontuario.objects.filter(paciente=paciente)
        consultas = Consulta.objects.filter(paciente=paciente)
        exames = Exame.objects.filter(prontuario__paciente=paciente)

        context = {
            "patient": paciente,
            "prontuarios": prontuarios,
            "consultas": consultas,
            "exames": exames
        }
        context.update(context_user_flags(request))

        return render(request, "agendamento/prontuarios/listar_prontuarios.html", context)

    # Médico — vê prontuários dos seus pacientes
    elif is_medico(user):
        medico = user.perfil_medico

        pacientes_ids = Consulta.objects.filter(
            medico=medico
        ).values_list("paciente_id", flat=True)

        prontuarios = Prontuario.objects.filter(
            paciente__in=pacientes_ids
        ).select_related("paciente")

        consultas = Consulta.objects.filter(medico=medico)
        exames = Exame.objects.filter(prontuario__paciente__in=pacientes_ids)

        context = {
            "patient": None,
            "prontuarios": prontuarios,
            "consultas": consultas,
            "exames": exames
        }
        context.update(context_user_flags(request))

        return render(request, "agendamento/prontuarios/listar_prontuarios.html", context)

    # Admin / secretaria — vê tudo
    else:
        prontuarios = Prontuario.objects.all().select_related("paciente")
        consultas = Consulta.objects.all()
        exames = Exame.objects.all()

        context = {
            "patient": None,
            "prontuarios": prontuarios,
            "consultas": consultas,
            "exames": exames
        }
        context.update(context_user_flags(request))

        return render(request, "agendamento/prontuarios/listar_prontuarios.html", context)


# ===============================================================
# PRONTUÁRIO — DETALHE
# ===============================================================

@login_required
def prontuario_detalhe(request, pk):
    prontuario = get_object_or_404(Prontuario, pk=pk)
    paciente = prontuario.paciente

    exames = Exame.objects.filter(prontuario=prontuario).order_by('-criado_em')
    consultas = Consulta.objects.filter(paciente=paciente).order_by('-data_hora')

    context = {
        "prontuario": prontuario,
        "paciente": paciente,
        "exames": exames,
        "consultas": consultas,
    }

    return render(request, "agendamento/prontuarios/prontuario_detalhe.html", context)

# ===============================================================
# PRONTUÁRIO — EDITAR
# ===============================================================

@login_required
def editar_prontuario(request, pk):
    prontuario = get_object_or_404(Prontuario, pk=pk)

    # Permissões: médico, secretaria ou admin
    if not (
        request.user.is_staff or request.user.is_superuser or
        hasattr(request.user, "perfil_medico")
    ):
        messages.error(request, "Você não tem permissão para editar este prontuário.")
        return redirect("listar_prontuarios")

    if request.method == "POST":

        # Botão cancelar
        if "cancelar" in request.POST:
            messages.info(request, "Edição cancelada.")
            return redirect("prontuario_detalhe", pk=pk)

        prontuario.descricao   = request.POST.get("descricao", "").strip()
        prontuario.queixa      = request.POST.get("queixa", "").strip()
        prontuario.diagnostico = request.POST.get("diagnostico", "").strip()
        prontuario.cid         = request.POST.get("cid", "").strip()
        prontuario.medicacao   = request.POST.get("medicacao", "").strip()

        # validações simples
        if prontuario.descricao == "":
            messages.error(request, "O campo descrição é obrigatório.")
            return redirect("editar_prontuario", pk=pk)

        if prontuario.diagnostico == "":
            messages.error(request, "O campo diagnóstico é obrigatório.")
            return redirect("editar_prontuario", pk=pk)

        # arquivo novo
        if request.FILES.get("arquivo"):
            arquivo = request.FILES["arquivo"]

            if arquivo.size > 10 * 1024 * 1024:
                messages.error(request, "Arquivo muito grande! Máximo 10MB.")
                return redirect("editar_prontuario", pk=pk)

            prontuario.anexo = arquivo

        prontuario.save()

        messages.success(request, "Prontuário atualizado com sucesso!")
        return redirect("prontuario_detalhe", pk=pk)

    # Método GET
    form = ProntuarioForm(instance=prontuario)

    return render(request, "agendamento/prontuarios/prontuario_form.html", {
        "form": form,
        "prontuario": prontuario,
        "edit_mode": True
    })


# ===============================================================
# PRONTUÁRIO — EDITAR COMPLETO
# ===============================================================

@login_required
def editar_prontuario_completo(request, pk):
    prontuario = get_object_or_404(Prontuario, pk=pk)
    paciente = prontuario.paciente

    exames = Exame.objects.filter(prontuario=prontuario).order_by("-criado_em")

    if request.method == "POST":
        prontuario.descricao = request.POST.get("descricao", "")
        prontuario.queixa = request.POST.get("queixa", "")
        prontuario.diagnostico = request.POST.get("diagnostico", "")
        prontuario.cid = request.POST.get("cid", "")
        prontuario.medicacao = request.POST.get("medicacao", "")

        # Novo documento principal
        if request.FILES.get("novo_documento"):
            prontuario.anexo = request.FILES["novo_documento"]

        # Novo exame anexado
        if request.FILES.get("novo_exame"):
            nome = request.POST.get("nome_exame", "")

            Exame.objects.create(
                prontuario=prontuario,
                arquivo=request.FILES["novo_exame"],
                nome=nome,
                observado_por=request.user
            )

        prontuario.save()

        messages.success(request, "Prontuário atualizado com sucesso!")
        return redirect("editar_prontuario_completo", pk=pk)

    context = {
        "prontuario": prontuario,
        "paciente": paciente,
        "exames": exames,
        "consultas": Consulta.objects.filter(paciente=paciente),
    }

    return render(request, "agendamento/prontuarios/prontuario_editar.html", context)


# ===============================================================
# PRONTUÁRIO — EXCLUIR
# ===============================================================

@login_required
def excluir_prontuario(request, pk):
    prontuario = get_object_or_404(Prontuario, pk=pk)

    if request.method == 'POST':
        prontuario.delete()
        messages.success(request, 'Prontuário excluído com sucesso!')
        return redirect('listar_prontuarios')

    context = {'prontuario': prontuario, 'titulo': 'Excluir Prontuário'}
    context.update(context_user_flags(request))

    return render(request, 'agendamento/prontuarios/prontuario_confirm_delete.html', context)


# ===============================================================
# EXAMES — UPLOAD
# ===============================================================

@login_required
def upload_exame(request, pk):
    prontuario = get_object_or_404(Prontuario, pk=pk)
    form = ExameForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        exame = form.save(commit=False)
        exame.prontuario = prontuario
        exame.observado_por = request.user
        exame.save()

        messages.success(request, "Exame enviado com sucesso!")
        return redirect("prontuario_detalhe", pk=pk)

    context = {
        "form": form,
        "prontuario": prontuario
    }
    context.update(context_user_flags(request))

    return render(request, "agendamento/exames/upload_exame.html", context)


# ===============================================================
# EXAMES — ANEXAR DOCUMENTO
# ===============================================================

@login_required
def anexar_exame(request, prontuario_id):
    prontuario = get_object_or_404(Prontuario, pk=prontuario_id)

    if request.method == "POST":
        arquivo = request.FILES.get("arquivo")
        nome = request.POST.get("nome")

        if arquivo and nome:
            Exame.objects.create(
                prontuario=prontuario,
                arquivo=arquivo,
                nome=nome,
                observado_por=request.user
            )

            messages.success(request, "Documento anexado com sucesso!")
            return redirect("prontuario_detalhe", pk=prontuario.pk)

        messages.error(request, "Erro ao enviar arquivo. Verifique os campos.")

    context = {"prontuario": prontuario}
    context.update(context_user_flags(request))

    return render(request, "agendamento/exames/anexar_exame.html", context)


# ===============================================================
# EXAMES — EXCLUIR EXAME
# ===============================================================

@login_required
def excluir_exame(request, exame_id):
    exame = get_object_or_404(Exame, pk=exame_id)

    prontuario_id = exame.prontuario.pk
    exame.delete()

    messages.success(request, "Exame removido com sucesso!")
    return redirect("editar_prontuario_completo", pk=prontuario_id)


# ===============================================================
# EXAMES — EXCLUIR DOCUMENTO
# ===============================================================

@login_required
def excluir_documento(request, doc_id):
    doc = get_object_or_404(Exame, pk=doc_id)

    prontuario_id = doc.prontuario.pk
    doc.delete()

    messages.success(request, "Documento removido com sucesso!")
    return redirect("editar_prontuario_completo", pk=prontuario_id)
