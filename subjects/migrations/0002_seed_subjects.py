from django.db import migrations

def create_seed_subjects(apps, schema_editor):
    Subject = apps.get_model('subjects', 'Subject')
    User = apps.get_model('accounts', 'User')

    instructor = User.objects.filter(username='instructor').first()

    pro101 = Subject.objects.create(
        name='Programación I',
        code='PRO101',
        credits=3,
        assigned_instructor=instructor
    )

    pro102 = Subject.objects.create(
        name='Programación II',
        code='PRO102',
        credits=3,
        assigned_instructor=instructor
    )
    pro102.prerequisites.add(pro101)

    bdd101 = Subject.objects.create(
        name='Bases de Datos I',
        code='BDD101',
        credits=4,
        assigned_instructor=instructor
    )

    edd101 = Subject.objects.create(
        name='Estructuras de Datos',
        code='EDD101',
        credits=3,
        assigned_instructor=instructor
    )
    edd101.prerequisites.add(pro101)

    alg101 = Subject.objects.create(
        name='Algoritmos',
        code='ALG101',
        credits=3,
        assigned_instructor=instructor
    )
    alg101.prerequisites.add(edd101)

    Subject.objects.create(
        name='Matemáticas Discretas',
        code='MAT101',
        credits=4
    )

    Subject.objects.create(
        name='Sistemas Operativos',
        code='SO101',
        credits=3,
        assigned_instructor=instructor
    )

def reverse_seed_subjects(apps, schema_editor):
    Subject = apps.get_model('subjects', 'Subject')
    Subject.objects.filter(code__in=['PRO101', 'PRO102', 'BDD101', 'EDD101', 'ALG101', 'MAT101', 'SO101']).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('subjects', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_seed_subjects, reverse_seed_subjects),
    ]
