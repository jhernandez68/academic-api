from django.db import migrations
from django.contrib.auth.hashers import make_password
from decimal import Decimal

def create_seed_enrollments(apps, schema_editor):
    Subject = apps.get_model('subjects', 'Subject')
    User = apps.get_model('accounts', 'User')
    Enrollment = apps.get_model('subjects', 'Enrollment')

    # Obtener estudiante y profesor
    student = User.objects.filter(username='student').first()
    instructor = User.objects.filter(username='instructor').first()

    if not student or not instructor:
        return

    # Obtener materias
    try:
        pro101 = Subject.objects.get(code='PRO101')
        bdd101 = Subject.objects.get(code='BDD101')
        so101 = Subject.objects.get(code='SO101')
        mat101 = Subject.objects.get(code='MAT101')
    except Subject.DoesNotExist:
        return

    # === DATOS PARA ESTUDIANTE ===

    # Inscripción en estado "enrolled" (sin calificación)
    Enrollment.objects.get_or_create(
        student=student,
        subject=pro101,
        defaults={'state': 'enrolled', 'grade': None}
    )

    # Inscripciones aprobadas con calificaciones
    Enrollment.objects.get_or_create(
        student=student,
        subject=bdd101,
        defaults={'state': 'approved', 'grade': Decimal('4.5')}
    )

    Enrollment.objects.get_or_create(
        student=student,
        subject=so101,
        defaults={'state': 'approved', 'grade': Decimal('4.0')}
    )

    # Inscripción reprobada
    Enrollment.objects.get_or_create(
        student=student,
        subject=mat101,
        defaults={'state': 'failed', 'grade': Decimal('2.5')}
    )

    # === DATOS PARA PROFESOR ===
    # Crear 2 estudiantes adicionales para las materias del profesor
    Student = apps.get_model('accounts', 'Student')
    Role = apps.get_model('accounts', 'Role')
    student_role = Role.objects.get(name='student')

    for i in range(2):
        user_data = {
            'username': f'student_test{i+2}',
            'email': f'student_test{i+2}@test.com',
            'first_name': f'Student',
            'last_name': f'Test{i+2}',
            'role_id': student_role.id
        }
        # Agregar password hasheada a los defaults
        user_data['password'] = make_password('testpass123')

        new_student, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults=user_data
        )

        if created:
            # Crear Student profile
            Student.objects.create(user=new_student)

        # Crear enrollments en materias con el profesor
        Enrollment.objects.get_or_create(
            student=new_student,
            subject=pro101,
            defaults={'state': 'enrolled', 'grade': None}
        )

        Enrollment.objects.get_or_create(
            student=new_student,
            subject=so101,
            defaults={'state': 'approved', 'grade': Decimal(str(3.5 + i * 0.5))}
        )

def reverse_seed_enrollments(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    Enrollment = apps.get_model('subjects', 'Enrollment')
    Student = apps.get_model('accounts', 'Student')

    # Eliminar enrollments del estudiante original
    student = User.objects.filter(username='student').first()
    if student:
        Enrollment.objects.filter(student=student).delete()

    # Eliminar estudiantes de prueba y sus enrollments
    for i in range(2):
        test_student = User.objects.filter(username=f'student_test{i+2}').first()
        if test_student:
            Enrollment.objects.filter(student=test_student).delete()
            # Eliminar Student profile si existe
            Student.objects.filter(user=test_student).delete()
            test_student.delete()

class Migration(migrations.Migration):
    dependencies = [
        ('subjects', '0002_seed_subjects'),
    ]

    operations = [
        migrations.RunPython(create_seed_enrollments, reverse_seed_enrollments),
    ]
