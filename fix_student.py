import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import User, Student

user = User.objects.get(username='student')
if not hasattr(user, 'student'):
    Student.objects.create(user=user)
    print('[OK] Student profile creado para usuario student')
else:
    print('[OK] Student profile ya existe')

# Verificar
user.refresh_from_db()
print(f'[OK] Max credits: {user.student.max_credits_per_term}')
