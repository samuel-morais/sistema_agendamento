from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from .models import Consulta, Paciente, Medico, Prontuario, Exame, Especialidade


# FORMULÁRIO DE CRIAÇÃO DE USUÁRIO

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user



# PACIENTE

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ['nome', 'cpf', 'telefone', 'email', 'data_nascimento']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'data_nascimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


# MÉDICOS

class MedicoForm(forms.ModelForm):
    class Meta:
        model = Medico
        fields = ['user', 'crm', 'especialidade', 'hora_inicio', 'hora_fim']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'crm': forms.TextInput(attrs={'class': 'form-control'}),
            'especialidade': forms.Select(attrs={'class': 'form-control'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_fim': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }



# ESPECIALIDADE

class EspecialidadeForm(forms.ModelForm):
    class Meta:
        model = Especialidade
        fields = ['nome']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
        }



# CONSULTA — Agendamento completo

class ConsultaForm(forms.ModelForm):
  
    data = forms.DateField(
        label="Data da consulta",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True
    )

    hora = forms.TimeField(
        label="Horário",
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        required=True
    )

    class Meta:
        model = Consulta
        fields = ['medico', 'observacoes', 'duracao_minutos', 'status', 'confirmada']
        widgets = {
            'medico': forms.Select(attrs={'class': 'form-select', 'id': 'id_medico'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.HiddenInput(),
            'confirmada': forms.HiddenInput(),
            'duracao_minutos': forms.HiddenInput(),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        # Carrega médicos com nome + especialidade
        self.fields['medico'].queryset = Medico.objects.select_related(
            'user', 'especialidade'
        ).all()

        self.fields['status'].initial = 'agendada'
        self.fields['confirmada'].initial = True
        self.fields['duracao_minutos'].initial = 30

    def clean(self):
        cleaned_data = super().clean()

        medico = cleaned_data.get('medico')
        data = cleaned_data.get('data')
        hora = cleaned_data.get('hora')
        duracao = cleaned_data.get('duracao_minutos') or 30

       
        # VALIDAÇÕES BÁSICAS
        
        if not medico:
            self.add_error('medico', 'Selecione um médico.')

        if not data:
            self.add_error('data', 'Data é obrigatória.')

        if not hora:
            self.add_error('hora', 'Horário é obrigatório.')

        # Se existem erros básicos, não continua
        if self.errors:
            raise ValidationError("Corrija os erros do formulário.")

        
        # COMBINAÇÃO DATA + HORA
        
        data_hora = datetime.combine(data, hora)
        data_hora = timezone.make_aware(data_hora)

        # Não permitir agendamento no passado
        if data_hora < timezone.now():
            raise ValidationError("⚠️ Não é possível agendar uma consulta no passado.")

        
        # VERIFICA CONFLITO
        
        fim_consulta = data_hora + timedelta(minutes=duracao)

        conflito = Consulta.objects.filter(
            medico=medico,
            data_hora__lt=fim_consulta,
            data_hora__gte=data_hora - timedelta(minutes=duracao),
            status__in=['agendada', 'confirmada']
        ).exclude(pk=self.instance.pk).exists()

        if conflito:
            raise ValidationError("⚠️ Este horário já está reservado para o médico escolhido.")

        cleaned_data['data_hora'] = data_hora
        cleaned_data['duracao_minutos'] = duracao
        return cleaned_data



# PRONTUÁRIO

class ProntuarioForm(forms.ModelForm):
    class Meta:
        model = Prontuario
        fields = ['paciente', 'descricao']
        widgets = {
            'paciente': forms.Select(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


# EXAMES

class ExameForm(forms.ModelForm):
    class Meta:
        model = Exame
        fields = ['prontuario', 'arquivo', 'nome']
        widgets = {
            'prontuario': forms.Select(attrs={'class': 'form-control'}),
            'arquivo': forms.FileInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_arquivo(self):
        arquivo = self.cleaned_data.get('arquivo')
        if arquivo and arquivo.size > 10 * 1024 * 1024:  # 10MB
            raise ValidationError("📁 Arquivo muito grande. Limite de 10 MB.")
        return arquivo
