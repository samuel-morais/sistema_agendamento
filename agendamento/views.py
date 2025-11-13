from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User, Group
from django.http import JsonResponse
from django.db import transaction
from datetime import datetime, time, timedelta

from .models import (
    Consulta, Paciente, Medico, Especialidade,
    Prontuario, Exame, Notificacao, Convenio
)
from .forms import (
    ConsultaForm, CustomUserCreationForm, PacienteForm, MedicoForm,
    EspecialidadeForm, ProntuarioForm, ExameForm
)


# ------------------------------------------
# FUNÇÕES AUXILIARES DE PERMISSÃO
# ------------------------------------------
def is_medico(user):
    return hasattr(user, 'perfil_medico')


def is_secretaria(user):
    return user.is_superuser or user.is_staff


def is_usuario_padrao(user):
    return user.groups.filter(name='Usuário Padrão').exists() if user.is_authenticated else False


def context_user_flags(request):
    return {
        'is_usuario_padrao': is_usuario_padrao(request.user),
        'is_medico_user': is_medico(request.user)
    }


# ------------------------------------------
# PÁGINA INICIAL / DASHBOARD
# ------------------------------------------
@login_required
def pagina_inicial(request):
    user = request.user
    context = {}

    # -----------------------------------
    # Usuário Médico
    # -----------------------------------
    if is_medico(user):
        medico = user.perfil_medico

        consultas = Consulta.objects.filter(
            medico=medico
        ).select_related("paciente", "medico__user").order_by("data_hora")

        prontuarios = Prontuario.objects.filter(
            paciente__consultas__medico=medico
        ).distinct()

        notificacoes = Notificacao.objects.filter(usuario=user).order_by('-criado_em')[:5]

        context.update({
            'consultas': consultas,
            'total_consultas': consultas.count(),
            'total_prontuarios': prontuarios.count(),
            'notificacoes': notificacoes,
        })

    # -----------------------------------
    # Usuário Padrão (Paciente)
    # -----------------------------------
    elif is_usuario_padrao(user):
        paciente = getattr(user, 'perfil_paciente', None)

        consultas = Consulta.objects.filter(
            paciente=paciente
        ).select_related("paciente", "medico__user").order_by("data_hora") if paciente else []

        prontuarios = Prontuario.objects.filter(paciente=paciente) if paciente else []

        notificacoes = Notificacao.objects.filter(usuario=user).order_by('-criado_em')[:5]

        context.update({
            'consultas': consultas,
            'total_consultas': len(consultas),
            'total_prontuarios': len(prontuarios),
            'total_exames': Exame.objects.filter(
                prontuario__paciente=paciente
            ).count() if paciente else 0,
            'notificacoes': notificacoes,
        })

    # -----------------------------------
    # Secretaria / Admin
    # -----------------------------------
    else:
        consultas = Consulta.objects.select_related(
            "paciente", "medico__user"
        ).order_by("data_hora")

        context.update({
            'consultas': consultas,
            'total_consultas': consultas.count(),
            'total_pacientes': Paciente.objects.count(),
            'total_medicos': Medico.objects.count(),
            'total_especialidades': Especialidade.objects.count(),
            'total_prontuarios': Prontuario.objects.count(),
            'total_exames': Exame.objects.count(),
            'notificacoes': Notificacao.objects.filter(usuario=user).order_by('-criado_em')[:5],
        })

        context.update({
            'consultas_pendentes': consultas.filter(status='agendada')[:10],
            'consultas_confirmadas': consultas.filter(status='confirmada')[:10],
            'consultas_canceladas': consultas.filter(status='cancelada')[:10],
        })

    context.update(context_user_flags(request))
    return render(request, 'agendamento/pagina_inicial.html', context)


# ------------------------------------------
# PERFIL DE USUÁRIO
# ------------------------------------------
@login_required
def perfil_usuario(request):
    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('perfil_usuario')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        form = UserChangeForm(instance=request.user)
    context = {'form': form, 'titulo': 'Meu Perfil'}
    context.update(context_user_flags(request))
    return render(request, 'agendamento/usuarios/perfil_usuario.html', context)


# ------------------------------------------
# CADASTRO DE USUÁRIO
# ------------------------------------------
def cadastrar_usuario(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            grupo, _ = Group.objects.get_or_create(name='Usuário Padrão')
            user.groups.add(grupo)
            messages.success(request, "Conta criada com sucesso! Faça login para continuar.")
            return redirect('login')
        else:
            messages.error(request, "Corrija os erros abaixo.")
    else:
        form = CustomUserCreationForm()
    context = {'form': form}
    context.update(context_user_flags(request))
    return render(request, 'agendamento/cadastrar.html', context)

def validar_username(request):
    username = request.GET.get("u", "")
    exists = User.objects.filter(username__iexact=username).exists()
    return JsonResponse({"exists": exists})

def validar_email(request):
    email = request.GET.get("e", "")
    exists = User.objects.filter(email__iexact=email).exists()
    return JsonResponse({"exists": exists})
# ------------------------------------------
# PACIENTES CRUD
# ------------------------------------------
@login_required
def listar_pacientes(request):
    pacientes = Paciente.objects.all().order_by('nome')
    context = {'pacientes': pacientes}
    context.update(context_user_flags(request))
    return render(request, 'agendamento/pacientes/listar_pacientes.html', context)


@login_required
def criar_paciente(request):
    form = PacienteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Paciente criado com sucesso!')
        return redirect('listar_pacientes')
    context = {'form': form, 'titulo': 'Novo Paciente'}
    context.update(context_user_flags(request))
    return render(request, 'agendamento/pacientes/paciente_form.html', context)


@login_required
def editar_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    form = PacienteForm(request.POST or None, instance=paciente)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Paciente atualizado com sucesso!')
        return redirect('listar_pacientes')
    context = {'form': form, 'titulo': 'Editar Paciente'}
    context.update(context_user_flags(request))
    return render(request, 'agendamento/pacientes/paciente_form.html', context)


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


@login_required
def historico_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    consultas = Consulta.objects.filter(
        paciente=paciente
    ).select_related('medico').order_by('-data_hora')
    context = {'paciente': paciente, 'consultas': consultas}
    context.update(context_user_flags(request))
    return render(request, 'agendamento/pacientes/historico_paciente.html', context)


# ------------------------------------------
# MÉDICOS CRUD
# ------------------------------------------
@login_required
@user_passes_test(is_secretaria)
def listar_medicos(request):
    medicos = Medico.objects.select_related('user', 'especialidade').all().order_by('user__first_name')
    context = {'medicos': medicos}
    context.update(context_user_flags(request))
    return render(request, 'agendamento/medicos/listar_medicos.html', context)


@login_required
@user_passes_test(is_secretaria)
def criar_medico(request):
    form = MedicoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Médico cadastrado com sucesso!')
        return redirect('listar_medicos')
    context = {'form': form, 'titulo': 'Novo Médico'}
    context.update(context_user_flags(request))
    return render(request, 'agendamento/medicos/medico_form.html', context)


@login_required
@user_passes_test(is_secretaria)
def editar_medico(request, pk):
    medico = get_object_or_404(Medico, pk=pk)
    form = MedicoForm(request.POST or None, instance=medico)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Médico atualizado com sucesso!')
        return redirect('listar_medicos')
    context = {'form': form, 'titulo': 'Editar Médico'}
    context.update(context_user_flags(request))
    return render(request, 'agendamento/medicos/medico_form.html', context)


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


# ------------------------------------------
# ESPECIALIDADES CRUD
# ------------------------------------------
@login_required
@user_passes_test(is_secretaria)
def listar_especialidades(request):
    especialidades = Especialidade.objects.all().order_by('nome')
    context = {'especialidades': especialidades}
    context.update(context_user_flags(request))
    return render(request, 'agendamento/especialidades/listar_especialidades.html', context)


@login_required
@user_passes_test(is_secretaria)
def criar_especialidade(request):
    form = EspecialidadeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Especialidade cadastrada com sucesso!')
        return redirect('listar_especialidades')
    context = {'form': form, 'titulo': 'Nova Especialidade'}
    context.update(context_user_flags(request))
    return render(request, 'agendamento/especialidades/especialidade_form.html', context)


@login_required
@user_passes_test(is_secretaria)
def editar_especialidade(request, pk):
    especialidade = get_object_or_404(Especialidade, pk=pk)
    form = EspecialidadeForm(request.POST or None, instance=especialidade)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Especialidade atualizada com sucesso!')
        return redirect('listar_especialidades')
    context = {'form': form, 'titulo': 'Editar Especialidade'}
    context.update(context_user_flags(request))
    return render(request, 'agendamento/especialidades/especialidade_form.html', context)


@login_required
@user_passes_test(is_secretaria)
def excluir_especialidade(request, pk):
    especialidade = get_object_or_404(Especialidade, pk=pk)
    if request.method == 'POST':
        especialidade.delete()
        messages.success(request, 'Especialidade excluída com sucesso!')
        return redirect('listar_especialidades')
    context = {'especialidade': especialidade, 'titulo': 'Excluir Especialidade'}
    context.update(context_user_flags(request))
    return render(request, 'agendamento/especialidades/especialidade_confirm_delete.html', context)


# ------------------------------------------
# CONSULTAS — listagem, criação, edição, cancelamento
# ------------------------------------------
@login_required
def listar_consultas(request):
    user = request.user
    context = {}

    if is_usuario_padrao(user):
        paciente = getattr(user, 'perfil_paciente', None)
        consultas = Consulta.objects.filter(paciente=paciente).order_by('-data_hora') if paciente else Consulta.objects.none()

    elif is_medico(user):
        medico = user.perfil_medico
        consultas = Consulta.objects.filter(medico=medico).order_by('-data_hora')
        Notificacao.objects.filter(usuario=user, lida=False).update(lida=True)

    else:
        consultas = Consulta.objects.all().order_by('-data_hora')

    for c in consultas:
        c.horario_bloqueado = c.status == 'agendada' and c.data_hora > timezone.now()

    context.update({
        'consultas': consultas,
        'notificacoes': Notificacao.objects.filter(usuario=user).order_by('-criado_em')[:5],
    })
    context.update(context_user_flags(request))
    return render(request, 'agendamento/consultas/listar_consultas.html', context)


@login_required
def criar_consulta(request):
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        form = ConsultaForm(request.POST, user=request.user)

        data = request.POST.get('data')
        hora = request.POST.get('hora')

        if data and hora:
            try:
                data_hora = datetime.strptime(f"{data} {hora}", "%Y-%m-%d %H:%M")
            except ValueError:
                data_hora = None
        else:
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

                    conflito = Consulta.objects.select_for_update().filter(
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
                    consulta.confirmada = True
                    consulta.usa_convenio = bool(usa_convenio)
                    consulta.convenio = convenio_obj if usa_convenio else None
                    consulta.save()

                    Notificacao.objects.create(
                        usuario=medico.user,
                        titulo="Nova consulta agendada",
                        mensagem=(
                            f"Paciente {consulta.paciente.nome} marcou uma consulta "
                            f"para {consulta.data_hora.strftime('%d/%m/%Y %H:%M')}."
                        ),
                        link=reverse('editar_consulta', args=[consulta.id])
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
            simplified = {}
            for field, errlist in errors.items():
                simplified[field] = [e['message'] for e in errlist]
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


@login_required
def confirmar_consulta(request, pk):
    if request.method != 'POST':
        return redirect('listar_consultas')
    consulta = get_object_or_404(Consulta, pk=pk)
    if not (is_medico(request.user) or request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Você não tem permissão para confirmar esta consulta.")
        return redirect('listar_consultas')
    consulta.status = 'confirmada'
    consulta.confirmada = True
    consulta.save()
    messages.success(request, "Consulta confirmada com sucesso!")
    return redirect('pagina_inicial')


def get_paciente_do_usuario(user):
    if hasattr(user, 'perfil_paciente'):
        return user.perfil_paciente
    paciente, _ = Paciente.objects.get_or_create(
        usuario=user,
        defaults={'nome': user.get_full_name() or user.username, 'email': user.email}
    )
    return paciente


@login_required
def editar_consulta(request, pk):
    consulta = get_object_or_404(Consulta, pk=pk)

    if not (is_secretaria(request.user) or is_medico(request.user) or consulta.paciente == getattr(request.user, 'perfil_paciente', None)):
        messages.error(request, 'Você não tem permissão para editar esta consulta.')
        return redirect('listar_consultas')

    if request.method == 'POST':
        form = ConsultaForm(request.POST, instance=consulta, user=request.user)
        if form.is_valid():
            data = form.cleaned_data['data']
            hora = form.cleaned_data['hora']
            duracao = form.cleaned_data.get('duracao_minutos') or consulta.duracao_minutos
            data_hora = timezone.make_aware(datetime.combine(data, hora), timezone.get_current_timezone())

            consulta.data_hora = data_hora
            consulta.medico = form.cleaned_data['medico']
            consulta.observacoes = form.cleaned_data['observacoes']
            consulta.status = form.cleaned_data['status']
            consulta.confirmada = form.cleaned_data['confirmada']
            consulta.duracao_minutos = duracao

            if 'usa_convenio' in form.cleaned_data:
                consulta.usa_convenio = form.cleaned_data.get('usa_convenio', False)
            if 'convenio' in form.cleaned_data:
                consulta.convenio = form.cleaned_data.get('convenio', None)

            consulta.save()

            messages.success(request, 'Consulta atualizada com sucesso!')
            return redirect('listar_consultas')
        else:
            messages.error(request, 'Corrija os erros do formulário.')
    else:
        inicial = {
            'data': consulta.data_hora.date(),
            'hora': consulta.data_hora.time().strftime('%H:%M'),
            'duracao_minutos': consulta.duracao_minutos,
        }
        form = ConsultaForm(instance=consulta, initial=inicial, user=request.user)

    context = {'form': form, 'titulo': 'Editar Consulta', 'consulta': consulta}
    context.update(context_user_flags(request))
    return render(request, 'agendamento/consultas/consulta_form.html', context)


@login_required
def excluir_consulta(request, pk):
    consulta = get_object_or_404(Consulta, pk=pk)

    if not (is_secretaria(request.user) or is_medico(request.user) or consulta.paciente == getattr(request.user, 'perfil_paciente', None)):
        messages.error(request, 'Você não tem permissão para excluir esta consulta.')
        return redirect('listar_consultas')

    if request.method == 'POST':
        consulta.delete()
        messages.success(request, 'Consulta excluída com sucesso!')
        return redirect('listar_consultas')

    context = {'consulta': consulta, 'titulo': 'Excluir Consulta'}
    context.update(context_user_flags(request))
    return render(request, 'agendamento/consultas/consulta_confirm_delete.html', context)


@login_required
def cancelar_consulta(request, pk):
    consulta = get_object_or_404(Consulta, pk=pk)

    if not (is_secretaria(request.user) or is_medico(request.user) or consulta.paciente == getattr(request.user, 'perfil_paciente', None)):
        messages.error(request, 'Você não tem permissão para cancelar esta consulta.')
        return redirect('listar_consultas')

    if request.method == 'POST':
        consulta.status = 'cancelada'
        consulta.save()
        messages.success(request, 'Consulta cancelada com sucesso!')
        return redirect('listar_consultas')

    context = {'consulta': consulta, 'titulo': 'Cancelar Consulta'}
    context.update(context_user_flags(request))
    return render(request, 'agendamento/consultas/consulta_confirm_cancel.html', context)


# ------------------------------------------
# HORÁRIOS DISPONÍVEIS
# ------------------------------------------
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
    except Medico.DoesNotExist:
        return JsonResponse({"horarios": []}, status=404)

    intervalo = timedelta(minutes=30)

    consultas = Consulta.objects.filter(
        medico_id=medico_id,
        data_hora__date=data_consulta,
        status__in=["agendada", "confirmada"]
    )

    horarios_ocupados = set()
    for c in consultas:
        local_time = timezone.localtime(c.data_hora)
        horarios_ocupados.add(local_time.strftime("%H:%M"))

    disponiveis = []
    atual = datetime.combine(data_consulta, hora_inicio)
    fim = datetime.combine(data_consulta, hora_fim)

    while atual < fim:
        hora_str = atual.strftime("%H:%M")
        if hora_str not in horarios_ocupados:
            disponiveis.append(hora_str)
        atual += intervalo

    return JsonResponse({"horarios": disponiveis})


def medicos_por_especialidade(request):
    especialidade_id = request.GET.get("especialidade_id")
    if not especialidade_id:
        return JsonResponse({"medicos": []})

    medicos = (
        Medico.objects.filter(especialidade_id=especialidade_id)
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
        if consultas_agendadas < 18:
            medicos_disponiveis.append({
                "id": medico.id,
                "nome": medico.user.get_full_name(),
                "especialidade": medico.especialidade.nome
            })

    return JsonResponse({"medicos": medicos_disponiveis})


# ------------------------------------------
# NOTIFICAÇÕES AO VIVO (para médicos)
# ------------------------------------------
@login_required
def notificacoes_novas(request):
    notificacoes = Notificacao.objects.filter(usuario=request.user, lida=False).order_by('-criado_em')
    data = [
        {
            'id': n.id,
            'titulo': n.titulo,
            'mensagem': n.mensagem,
            'link': n.link,
            'criado_em': n.criado_em.strftime('%d/%m/%Y %H:%M'),
        }
        for n in notificacoes
    ]

    notificacoes.update(lida=True)
    return JsonResponse({'novas': data})


# ------------------------------------------
# PRONTUÁRIOS E EXAMES
# ------------------------------------------
@login_required
def criar_prontuario(request):
    form = ProntuarioForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Prontuário criado com sucesso!')
        return redirect('listar_prontuarios')
    context = {'form': form, 'titulo': 'Novo Prontuário'}
    context.update(context_user_flags(request))
    return render(request, 'agendamento/prontuarios/prontuario_form.html', context)


@login_required
def listar_prontuarios(request):
    if is_medico(request.user):
        prontuarios = Prontuario.objects.filter(
            paciente__consultas__medico=request.user.perfil_medico
        ).distinct()
    else:
        prontuarios = Prontuario.objects.all()
    context = {'prontuarios': prontuarios}
    context.update(context_user_flags(request))
    return render(request, 'agendamento/prontuarios/listar_prontuarios.html', context)


@login_required
def editar_prontuario(request, pk):
    prontuario = get_object_or_404(Prontuario, pk=pk)
    form = ProntuarioForm(request.POST or None, instance=prontuario)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Prontuário atualizado com sucesso!')
        return redirect('listar_prontuarios')
    context = {'form': form, 'titulo': 'Editar Prontuário'}
    context.update(context_user_flags(request))
    return render(request, 'agendamento/prontuarios/prontuario_form.html', context)


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


@login_required
def upload_exame(request):
    form = ExameForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        exame = form.save(commit=False)
        exame.observado_por = request.user
        exame.save()
        messages.success(request, 'Exame enviado com sucesso!')
        return redirect('listar_prontuarios')
    context = {'form': form, 'titulo': 'Fazer Upload de Exame'}
    context.update(context_user_flags(request))
    return render(request, 'agendamento/exames/upload_exame.html', context)
