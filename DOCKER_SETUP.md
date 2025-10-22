# Docker Setup - Academic API

Guía completa para ejecutar la aplicación usando Docker Compose.

## 📋 Requisitos

- Docker (versión 20.10+)
- Docker Compose (versión 2.0+)

## 🚀 Inicio Rápido

### 1. Preparar el entorno

```bash
# Copiar archivo de configuración para Docker
cp .env.docker .env
```

### 2. Construir e iniciar servicios

```bash
# Construir imagen y levantar todos los servicios
docker-compose up -d

# O sin detached mode (para ver logs en vivo)
docker-compose up
```

### 3. Verificar que todo esté funcionando

```bash
# Ver status de los servicios
docker-compose ps

# Ver logs de un servicio específico
docker-compose logs web
docker-compose logs celery_worker
docker-compose logs postgres
```

## 🔧 Servicios Incluidos

| Servicio | Puerto | URL |
|----------|--------|-----|
| Django API | 8000 | http://localhost:8000 |
| PostgreSQL | 5432 | postgres://localhost:5432 |
| Redis | 6379 | redis://localhost:6379 |
| Celery Worker | - | - |
| Celery Beat | - | - |

## 📚 Usar la API

### Obtener Token JWT

```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Acceder a Swagger

```
http://localhost:8000/swagger/
```

### Acceder a ReDoc

```
http://localhost:8000/redoc/
```

## 🧪 Ejecutar Tests

```bash
# Ejecutar tests dentro del contenedor
docker-compose exec web pytest tests_flujos.py -v

# Ejecutar tests críticos
docker-compose exec web pytest tests_critical_endpoints.py -v

# Ejecutar todos los tests
docker-compose exec web pytest -v
```

## 🗃️ Gestión de Base de Datos

```bash
# Ejecutar migraciones
docker-compose exec web python manage.py migrate

# Crear superuser
docker-compose exec web python manage.py createsuperuser

# Shell interactivo
docker-compose exec web python manage.py shell

# Ver logs de PostgreSQL
docker-compose logs postgres
```

## 🐍 Python Shell

```bash
# Acceder a Django shell dentro del contenedor
docker-compose exec web python manage.py shell
```

## 📊 Monitorar Celery

```bash
# Ver tareas activas
docker-compose exec celery_worker celery -A core inspect active

# Ver workers disponibles
docker-compose exec celery_worker celery -A core inspect registered
```

## 🛑 Detener Servicios

```bash
# Detener todos los servicios
docker-compose down

# Detener y eliminar datos (ADVERTENCIA: perderá datos)
docker-compose down -v
```

## 🔄 Reiniciar Servicios

```bash
# Reiniciar un servicio específico
docker-compose restart web

# Reiniciar todos
docker-compose restart
```

## 📝 Credenciales de Prueba

| Usuario | Password | Rol |
|---------|----------|-----|
| admin | admin123 | Admin |
| instructor | instructor123 | Instructor |
| student | student123 | Student |

*Nota: Estas credenciales se crean automáticamente en la primera ejecución*

## 🔍 Troubleshooting

### El puerto 8000 está en uso

```bash
# Encontrar proceso usando puerto 8000
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Cambiar puerto en docker-compose.yml
# Modificar "8000:8000" a "8001:8000" por ejemplo
```

### PostgreSQL no inicia

```bash
# Verificar logs
docker-compose logs postgres

# Reconstruir con fresh data
docker-compose down -v
docker-compose up -d
```

### Celery no procesa tareas

```bash
# Ver logs del worker
docker-compose logs celery_worker

# Reiniciar worker
docker-compose restart celery_worker
```

## 📦 Estructura Docker

```
.
├── Dockerfile              # Imagen de la aplicación Django
├── docker-compose.yml      # Configuración de servicios
├── .dockerignore          # Archivos a ignorar en imagen
├── .env.docker            # Variables de entorno para Docker
└── requirements.txt       # Dependencias Python
```

## 🎯 Próximos Pasos

1. Verificar que todos los servicios estén saludables: `docker-compose ps`
2. Acceder a la API: http://localhost:8000/api/
3. Ejecutar tests: `docker-compose exec web pytest -v`
4. Explorar endpoints en Swagger: http://localhost:8000/swagger/

## 📞 Soporte

Para más información sobre los endpoints, ver:
- `README.md` - Documentación de la API
- `TESTING_GUIDE.md` - Guía de pruebas completa
- `docs/` - Documentación adicional
