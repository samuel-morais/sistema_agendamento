from django.db import models
from django.contrib.auth.models import User

class Especialidade(models.Model):
    nome = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nome

class Medico(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    crm = models.CharField(max_length=20)
    especialidade = models.ForeignKey(Especialidade, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.get_full_name()

class Paciente(models.Model):
    nome = models.CharField(max_length=150)
    cpf = models.CharField(max_length=14)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    data_nascimento = models.DateField()

    def __str__(self):
        return self.nome

class Consulta(models.Model):
    STATUS_CHOICES = [
        ('agendada', 'Agendada'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada'),
    ]
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE)
    data_hora = models.DateTimeField()
    duracao_minutos = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='agendada')
    exames = models.TextField(blank=True)

    def __str__(self):
        return f"{self.paciente} - {self.medico} - {self.data_hora}"
