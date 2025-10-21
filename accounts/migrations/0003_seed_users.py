from django.db import migrations
from django.contrib.auth.hashers import make_password

def create_seed_users(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    Role = apps.get_model('accounts', 'Role')

    admin_role = Role.objects.get(name='admin')
    instructor_role = Role.objects.get(name='instructor')
    student_role = Role.objects.get(name='student')

    User.objects.create(
        username='admin',
        email='admin@alternova.com',
        first_name='Admin',
        last_name='User',
        password=make_password('admin123'),
        is_staff=True,
        is_superuser=True,
        role=admin_role
    )

    User.objects.create(
        username='instructor',
        email='instructor@alternova.com',
        first_name='Instructor',
        last_name='User',
        password=make_password('instructor123'),
        role=instructor_role
    )

    User.objects.create(
        username='student',
        email='student@alternova.com',
        first_name='Student',
        last_name='User',
        password=make_password('student123'),
        role=student_role
    )

def reverse_seed_users(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.filter(username__in=['admin', 'instructor', 'student']).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0002_populate_roles'),
    ]

    operations = [
        migrations.RunPython(create_seed_users, reverse_seed_users),
    ]
