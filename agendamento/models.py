# ===============================================================
# IMPORTAÇÕES
# ===============================================================

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# ===============================================================
# ESPECIALIDADE
# ===============================================================

class Especialidade(models.Model):
    nome = models.CharField(max_length=150)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


# ===============================================================
# CONVÊNIO
# ===============================================================

class Convenio(models.Model):
    nome = models.CharField(max_length=150)
    codigo = models.CharField(max_length=50, null=True, blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


# ===============================================================
# PACIENTE
# ===============================================================

class Paciente(models.Model):
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="perfil_paciente",
        null=True,
        blank=True
    )

    nome = models.CharField(max_length=150)
    cpf = models.CharField(max_length=14, unique=True, null=True, blank=True)

    rg = models.CharField(max_length=20, null=True, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    data_nascimento = models.DateField(null=True, blank=True)
    endereco = models.CharField(max_length=255, null=True, blank=True)

    convenio = models.ForeignKey(
        Convenio,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='pacientes'
    )

    foto = models.ImageField(upload_to="fotos_perfil/", null=True, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


# ===============================================================
# MÉDICO
# ===============================================================

class Medico(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="perfil_medico"
    )
    crm = models.CharField(max_length=20)
    especialidade = models.ForeignKey(
        Especialidade,
        on_delete=models.SET_NULL,
        null=True,
        related_name="medicos"
    )
    hora_inicio = models.TimeField(null=True, blank=True)
    hora_fim = models.TimeField(null=True, blank=True)

    class Meta:
        ordering = ["user__first_name"]

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.especialidade})"


# ===============================================================
# CONSULTA
# ===============================================================

STATUS_CHOICES = (
    ("agendada", "Agendada"),
    ("confirmada", "Confirmada"),
    ("cancelada", "Cancelada"),
    ("realizada", "Realizada"),
)


class Consulta(models.Model):
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="consultas"
    )
    medico = models.ForeignKey(
        Medico,
        on_delete=models.CASCADE,
        related_name="consultas"
    )
    usuario = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="consultas_criadas"
    )

    data_hora = models.DateTimeField()
    duracao_minutos = models.PositiveIntegerField(default=30)

    observacoes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="agendada"
    )
    confirmada = models.BooleanField(default=False)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    usa_convenio = models.BooleanField(default=False)
    convenio = models.ForeignKey(
        Convenio,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="consultas"
    )

    class Meta:
        ordering = ["-data_hora"]

    def __str__(self):
        return f"{self.paciente} — {self.medico} — {self.data_hora.strftime('%d/%m/%Y %H:%M')}"


# ===============================================================
# PRONTUÁRIO
# ===============================================================

class Prontuario(models.Model):
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="prontuarios"
    )
    medico = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Informações médicas
    descricao = models.TextField(blank=True, null=True)
    queixa = models.TextField(blank=True, null=True)
    diagnostico = models.TextField(blank=True, null=True)
    cid = models.CharField(max_length=20, blank=True, null=True)
    medicacao = models.TextField(blank=True, null=True)
    anexo = models.FileField(upload_to="prontuarios/anexos/", blank=True, null=True)

    # Dados clínicos
    temperatura = models.CharField(max_length=10, blank=True, null=True)
    pressao = models.CharField(max_length=20, blank=True, null=True)
    saturacao = models.CharField(max_length=10, blank=True, null=True)
    frequencia_cardiaca = models.CharField(max_length=10, blank=True, null=True)
    frequencia_respiratoria = models.CharField(max_length=10, blank=True, null=True)

    exame_fisico = models.TextField(blank=True, null=True)
    conduta = models.TextField(blank=True, null=True)
    evolucao = models.TextField(blank=True, null=True)

    criado_em = models.DateTimeField(default=timezone.now)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Prontuário #{self.pk} - {self.paciente.nome}"


# ===============================================================
# EXAME
# ===============================================================

class Exame(models.Model):
    prontuario = models.ForeignKey(
        Prontuario,
        on_delete=models.CASCADE,
        related_name="exames"
    )
    arquivo = models.FileField(upload_to="exames/")
    nome = models.CharField(max_length=200)
    observado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="exames_observados"
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome


# ===============================================================
# NOTIFICAÇÃO
# ===============================================================

class Notificacao(models.Model):
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notificacoes"
    )
    titulo = models.CharField(max_length=200)
    mensagem = models.TextField()
    link = models.CharField(max_length=300, null=True, blank=True)
    lida = models.BooleanField(default=False)
    criado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.titulo} - {self.usuario}"
