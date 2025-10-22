#!/bin/bash

# Entrypoint script para el contenedor Django

set -e

echo "🚀 Iniciando Academic API..."

# Esperar a que PostgreSQL esté listo
echo "⏳ Esperando a PostgreSQL..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "✅ PostgreSQL está listo"

# Esperar a que Redis esté listo
echo "⏳ Esperando a Redis..."
while ! nc -z redis 6379; do
  sleep 1
done
echo "✅ Redis está listo"

# Ejecutar migraciones
echo "🔄 Ejecutando migraciones..."
python manage.py migrate

# Crear superuser si no existe
echo "👤 Verificando superuser..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("✅ Superuser 'admin' creado")
else:
    print("✅ Superuser 'admin' ya existe")
END

# Recopilar archivos estáticos
echo "📦 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

echo "✅ Configuración completada"
echo "🎯 Academic API está listo"

# Ejecutar comando pasado
exec "$@"
