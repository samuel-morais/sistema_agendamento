# ===============================================================
# IMPORTAÇÕES
# ===============================================================

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from .models import Consulta, Paciente, Medico, Prontuario, Exame, Especialidade, Convenio

import re


# ===============================================================
# FUNÇÕES AUXILIARES
# ===============================================================

def limpar_numero(valor):
    return re.sub(r'\D', '', valor or "")


def validar_cpf(cpf):
    cpf = limpar_numero(cpf)

    if not cpf or len(cpf) != 11 or cpf == cpf[0] * 11:
        raise ValidationError("CPF inválido.")

    def digito(v):
        soma = sum(int(v[i]) * (len(v) + 1 - i) for i in range(len(v)))
        d = (soma * 10) % 11
        return d if d < 10 else 0

    if digito(cpf[:9]) != int(cpf[9]) or digito(cpf[:10]) != int(cpf[10]):
        raise ValidationError("CPF inválido.")

    return cpf


def validar_telefone(telefone):
    telefone = limpar_numero(telefone)
    if len(telefone) not in (10, 11):
        raise ValidationError("Telefone inválido.")
    return telefone


def validar_nome(nome):
    if not nome or len(nome.strip().split()) < 2:
        raise ValidationError("Informe nome e sobrenome.")
    return nome


# ===============================================================
# USUÁRIO — CRIAÇÃO DE CONTA
# ===============================================================

class CustomUserCreationForm(UserCreationForm):

    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    cpf = forms.CharField(
        label="CPF",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000.000.000-00',
            'maxlength': '14'
        })
    )

    telefone = forms.CharField(
        label="Telefone",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '(00) 00000-0000',
            'maxlength': '15'
        })
    )

    class Meta:
        model = User
        fields = ("username", "email", "cpf", "telefone", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email=email).exists():
            raise ValidationError("Este email já está cadastrado.")
        return email

    def clean_cpf(self):
        cpf = self.cleaned_data.get("cpf")
        if not cpf:
            return cpf
        cpf_val = validar_cpf(cpf)

        if Paciente.objects.filter(cpf=cpf_val).exists():
            raise ValidationError("Este CPF já está cadastrado.")
        return cpf_val

    def clean_telefone(self):
        telefone = self.cleaned_data.get("telefone")
        if telefone:
            return validar_telefone(telefone)
        return telefone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email")

        if commit:
            user.save()

            Paciente.objects.create(
                usuario=user,
                nome=user.get_full_name() or user.username,
                cpf=limpar_numero(self.cleaned_data.get("cpf") or ""),
                telefone=limpar_numero(self.cleaned_data.get("telefone") or ""),
                email=user.email
            )

        return user


# ===============================================================
# PACIENTE — FORMULÁRIO
# ===============================================================

class PacienteForm(forms.ModelForm):

    def clean_nome(self):
        return validar_nome(self.cleaned_data.get("nome"))

    def clean_cpf(self):
        cpf_raw = self.cleaned_data.get("cpf")
        if not cpf_raw:
            return cpf_raw
        cpf_val = validar_cpf(cpf_raw)

        qs = Paciente.objects.filter(cpf=cpf_val)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("CPF já utilizado em outro paciente.")
        return cpf_val

    def clean_telefone(self):
        telefone = self.cleaned_data.get("telefone")
        if telefone:
            return validar_telefone(telefone)
        return telefone

    class Meta:
        model = Paciente
        fields = ['nome', 'cpf', 'telefone', 'email', 'data_nascimento']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '000.000.000-00',
                'maxlength': '14',
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(00) 00000-0000',
                'maxlength': '15',
            }),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'data_nascimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


# ===============================================================
# MÉDICO — FORMULÁRIO
# ===============================================================

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


# ===============================================================
# ESPECIALIDADE — FORMULÁRIO
# ===============================================================

class EspecialidadeForm(forms.ModelForm):

    class Meta:
        model = Especialidade
        fields = ['nome']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
        }


# ===============================================================
# CONSULTA — FORMULÁRIO COMPLETO
# ===============================================================

class ConsultaForm(forms.ModelForm):

    data = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    hora = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )

    class Meta:
        model = Consulta
        fields = ['medico', 'observacoes', 'duracao_minutos', 'status', 'confirmada']
        widgets = {
            'medico': forms.Select(attrs={'class': 'form-select'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control'}),
            'status': forms.HiddenInput(),
            'confirmada': forms.HiddenInput(),
            'duracao_minutos': forms.HiddenInput(),
        }

    # Permite ConsultaForm(user=request.user)
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        self.fields['medico'].queryset = Medico.objects.select_related("especialidade", "user")

        self.fields['status'].initial = 'agendada'
        self.fields['confirmada'].initial = True
        self.fields['duracao_minutos'].initial = 30

    def clean(self):
        cleaned = super().clean()

        medico = cleaned.get('medico')
        data = cleaned.get('data')
        hora = cleaned.get('hora')
        duracao = cleaned.get('duracao_minutos') or 30

        if not medico or not data or not hora:
            raise ValidationError("Preencha todos os campos obrigatórios.")

        data_hora = timezone.make_aware(datetime.combine(data, hora))

        if data_hora < timezone.now():
            raise ValidationError("Não é possível agendar uma consulta no passado.")

        fim = data_hora + timedelta(minutes=duracao)

        conflito = Consulta.objects.filter(
            medico=medico,
            data_hora__lt=fim,
            data_hora__gte=data_hora - timedelta(minutes=duracao),
            status__in=['agendada', 'confirmada']
        ).exclude(pk=self.instance.pk).exists()

        if conflito:
            raise ValidationError("Este horário já está reservado.")

        cleaned['data_hora'] = data_hora
        cleaned['duracao_minutos'] = duracao
        return cleaned


# ===============================================================
# EXAME — FORMULÁRIO
# ===============================================================

class ExameForm(forms.ModelForm):
    class Meta:
        model = Exame
        fields = ['prontuario', 'arquivo', 'nome']


# ===============================================================
# PERFIL DO PACIENTE — FORMULÁRIO DE EDIÇÃO
# ===============================================================

class UserPacienteProfileForm(UserChangeForm):
    password = None

    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control form-control-lg'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control form-control-lg'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control form-control-lg'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control form-control-lg'}))

    cpf = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control form-control-lg'}))
    telefone = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control form-control-lg'}))
    endereco = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control form-control-lg'}))

    convenio = forms.ModelChoiceField(
        queryset=Convenio.objects.filter(ativo=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-lg'})
    )

    rg = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control form-control-lg'}))
    data_nascimento = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control form-control-lg', 'type': 'date'})
    )

    foto = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control form-control-lg'}))

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.get("instance")
        super().__init__(*args, **kwargs)

        paciente = getattr(self.user, "perfil_paciente", None)

        if paciente:
            self.fields['cpf'].initial = paciente.cpf
            self.fields['telefone'].initial = paciente.telefone
            self.fields['endereco'].initial = paciente.endereco
            self.fields['convenio'].initial = paciente.convenio
            self.fields['rg'].initial = paciente.rg
            self.fields['data_nascimento'].initial = paciente.data_nascimento

    def save(self, commit=True):
        user = super().save(commit=commit)

        paciente = getattr(user, "perfil_paciente", None)

        if paciente:
            paciente.cpf = limpar_numero(self.cleaned_data.get("cpf") or "")
            paciente.telefone = limpar_numero(self.cleaned_data.get("telefone") or "")
            paciente.endereco = self.cleaned_data.get("endereco")
            paciente.convenio = self.cleaned_data.get("convenio")
            paciente.rg = self.cleaned_data.get("rg")
            paciente.data_nascimento = self.cleaned_data.get("data_nascimento")

            if self.cleaned_data.get("foto"):
                paciente.foto = self.cleaned_data["foto"]

            paciente.save()

        return user
