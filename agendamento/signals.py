from django.contrib.auth.models import User, Group, Permission
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .models import Paciente


# ===============================================================
# GRUPOS E USUÁRIOS PADRÃO (AUTOMÁTICO APÓS MIGRAÇÕES)
# ===============================================================

@receiver(post_migrate)
def criar_usuarios_e_grupos_padrao(sender, **kwargs):
    grupos = {
        'Secretaria': {
            'descricao': 'Acesso completo ao sistema',
            'permissoes': Permission.objects.all()
        },
        'Medico': {
            'descricao': 'Acesso restrito às suas consultas e prontuários',
            'permissoes': []
        }
    }

    # Criar grupos
    for nome, info in grupos.items():
        grupo, criado = Group.objects.get_or_create(name=nome)
        if info['permissoes']:
            grupo.permissions.set(info['permissoes'])
        grupo.save()

    # Usuário SECRETARIA padrão
    if not User.objects.filter(username='secretaria').exists():
        secretaria = User.objects.create_user(
            username='secretaria',
            first_name='Secretária',
            email='secretaria@hospital.com',
            password='Senha1234'
        )
        secretaria.is_staff = True
        secretaria.is_superuser = True
        secretaria.save()
        grupo_secretaria = Group.objects.get(name='Secretaria')
        secretaria.groups.add(grupo_secretaria)
        print("✅ Usuário Secretária criado: secretaria / Senha1234")

    # Usuário MÉDICO padrão
    if not User.objects.filter(username='medico').exists():
        medico_user = User.objects.create_user(
            username='medico',
            first_name='Médico',
            email='medico@hospital.com',
            password='Senha1234'
        )
        medico_user.is_staff = False
        medico_user.save()

        grupo_medico = Group.objects.get(name='Medico')
        medico_user.groups.add(grupo_medico)

        print("✅ Usuário Médico criado: medico / Senha1234")


# ===============================================================
# CRIAÇÃO AUTOMÁTICA DE PACIENTE PARA USUÁRIOS NOVOS
# ===============================================================

@receiver(post_save, sender=User)
def criar_paciente_para_usuario(sender, instance, created, **kwargs):

    if not created:
        return

    # Evitar duplicação — verificar o related_name correto
    if not hasattr(instance, "perfil_paciente"):
        Paciente.objects.create(
            usuario=instance,
            nome=instance.get_full_name() or instance.username,
            email=instance.email
        )
        print(f"✅ Paciente criado automaticamente para o usuário: {instance.username}")
