# 🐳 Docker - Quick Start

Cómo ejecutar la aplicación con Docker en 5 minutos.

## 1️⃣ Requisitos

- Docker instalado
- Docker Compose instalado

## 2️⃣ Inicio

### Opción A: Comando Simple

```bash
# Levanta todos los servicios
docker-compose up -d

# Ver status
docker-compose ps

# Ver logs
docker-compose logs -f web
```

### Opción B: Con Script (Recomendado)

```bash
# Iniciar
./docker-utils.sh start

# Ver logs
./docker-utils.sh logs web

# Detener
./docker-utils.sh stop
```

## 3️⃣ Acceder a la API

```
http://localhost:8000/
http://localhost:8000/swagger/
http://localhost:8000/redoc/
```

## 4️⃣ Credenciales por Defecto

```
Usuario: admin
Contraseña: admin123
```

## 5️⃣ Comandos Útiles

```bash
# Ver todos los servicios
docker-compose ps

# Ver logs de un servicio
docker-compose logs -f web          # Django
docker-compose logs -f postgres     # PostgreSQL
docker-compose logs -f redis        # Redis
docker-compose logs -f celery_worker

# Ejecutar tests
docker-compose exec web pytest tests_flujos.py -v

# Django shell
docker-compose exec web python manage.py shell

# Migraciones
docker-compose exec web python manage.py migrate

# Parar todo
docker-compose down

# Parar y borrar datos
docker-compose down -v
```

## 📊 Servicios

| Servicio | Puerto | Salud |
|----------|--------|-------|
| Django | 8000 | http://localhost:8000/swagger/ |
| PostgreSQL | 5432 | Integrada en compose |
| Redis | 6379 | Integrada en compose |
| Celery | - | Automático |

## 🔧 Troubleshooting

**Si algo no funciona:**

```bash
# Ver logs completos
docker-compose logs

# Reconstruir imagen
docker-compose build --no-cache

# Fresh start (perderá datos)
docker-compose down -v
docker-compose up -d

# Ver si los contenedores están corriendo
docker ps
```

## ✅ Verificar que funciona

```bash
# 1. Obtener token
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 2. Usar token para acceder a un endpoint
curl -X GET http://localhost:8000/api/accounts/statistics/ \
  -H "Authorization: Bearer <token_aqui>"
```

## 📚 Documentación Completa

Ver `DOCKER_SETUP.md` para más detalles.
