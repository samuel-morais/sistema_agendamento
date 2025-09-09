from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Consulta, Paciente, Medico
from .forms import ConsultaForm, PacienteForm, MedicoForm

@login_required
def pagina_inicial(request):
    total_consultas = Consulta.objects.count()
    total_pacientes = Paciente.objects.count()
    total_medicos = Medico.objects.count()
    return render(request, 'agendamento/pagina_inicial.html', {
        'total_consultas': total_consultas,
        'total_pacientes': total_pacientes,
        'total_medicos': total_medicos,
    })

# CRUD Consultas
@login_required
def listar_consultas(request):
    consultas = Consulta.objects.select_related('paciente', 'medico__user').all().order_by('data_hora')
    return render(request, 'agendamento/listar_consultas.html', {'consultas': consultas})

@login_required
def criar_consulta(request):
    form = ConsultaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('listar_consultas')
    return render(request, 'agendamento/consultas_form.html', {'form': form, 'titulo': 'Nova Consulta'})


@login_required
def editar_consulta(request, pk):
    consulta = get_object_or_404(Consulta, pk=pk)
    form = ConsultaForm(request.POST or None, instance=consulta)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('listar_consultas')
    return render(request, 'agendamento/consulta_form.html', {'form': form, 'titulo': 'Editar Consulta'})

@login_required
def excluir_consulta(request, pk):
    consulta = get_object_or_404(Consulta, pk=pk)
    if request.method == 'POST':
        consulta.delete()
        return redirect('listar_consultas')
    return render(request, 'agendamento/consulta_confirm_delete.html', {'consulta': consulta})

# CRUD Pacientes
@login_required
def listar_pacientes(request):
    pacientes = Paciente.objects.all().order_by('nome')
    return render(request, 'agendamento/listar_pacientes.html', {'pacientes': pacientes})

@login_required
def criar_paciente(request):
    form = PacienteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('listar_pacientes')
    return render(request, 'agendamento/paciente_form.html', {'form': form, 'titulo': 'Novo Paciente'})

@login_required
def editar_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    form = PacienteForm(request.POST or None, instance=paciente)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('listar_pacientes')
    return render(request, 'agendamento/paciente_form.html', {'form': form, 'titulo': 'Editar Paciente'})

@login_required
def excluir_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    if request.method == 'POST':
        paciente.delete()
        return redirect('listar_pacientes')
    return render(request, 'agendamento/paciente_confirm_delete.html', {'paciente': paciente})

# CRUD Médicos
@login_required
def listar_medicos(request):
    medicos = Medico.objects.select_related('user').all().order_by('user__first_name')
    return render(request, 'agendamento/listar_medicos.html', {'medicos': medicos})

@login_required
def criar_medico(request):
    form = MedicoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('listar_medicos')
    return render(request, 'agendamento/medico_form.html', {'form': form, 'titulo': 'Novo Médico'})

@login_required
def editar_medico(request, pk):
    medico = get_object_or_404(Medico, pk=pk)
    form = MedicoForm(request.POST or None, instance=medico)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('listar_medicos')
    return render(request, 'agendamento/medico_form.html', {'form': form, 'titulo': 'Editar Médico'})

@login_required
def excluir_medico(request, pk):
    medico = get_object_or_404(Medico, pk=pk)
    if request.method == 'POST':
        medico.delete()
        return redirect('listar_medicos')
    return render(request, 'agendamento/medico_confirm_delete.html', {'medico': medico})
