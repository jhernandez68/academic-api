from django.db import migrations

def create_roles(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    Role.objects.bulk_create([
        Role(name='admin', display_name='Administrador', description='Administrador del sistema'),
        Role(name='instructor', display_name='Instructor', description='Profesor o instructor'),
        Role(name='student', display_name='Estudiante', description='Estudiante'),
    ])

def reverse_roles(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    Role.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_roles, reverse_roles),
    ]
