# Academic API - Django Backend

Sistema de gestión académica para universidades con usuarios, materias, inscripciones, calificaciones, notificaciones y reportes.

## ⚡ Quick Start

**Con Docker (Recomendado):**
```bash
docker-compose up -d
# API en http://localhost:8000/swagger/
```

**Local (Sin Docker):**
```bash
python -m venv .venv
source .venv/Scripts/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

---

## 🚀 Instalación Local (Detallado)

### 1. Requisitos Previos
- Python 3.12+
- pip
- git (opcional)

### 2. Clonar/Navegar al Proyecto
```bash
cd academic-api
```

### 3. Crear Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 5. Configurar Base de Datos
```bash
# Copiar variables de entorno
cp .env.example .env

# Ejecutar migraciones
python manage.py migrate
```

### 6. (Opcional) Crear Superuser
```bash
python manage.py createsuperuser
# O usar predeterminado: admin / admin123
```

### 7. Ejecutar Servidor
```bash
python manage.py runserver
```

Accede a: http://localhost:8000/swagger/

---

## 🐳 Instalación con Docker

### 1. Requisitos Previos
- Docker
- Docker Compose

### 2. Quick Start
```bash
# Iniciar todos los servicios
docker-compose up -d

# Verificar estado
docker-compose ps

# Ver logs
docker-compose logs -f web
```

### 3. Acceder a la API
```
API: http://localhost:8000/
Swagger: http://localhost:8000/swagger/
ReDoc: http://localhost:8000/redoc/
```

### 4. Comandos Útiles
```bash
# Ver logs de un servicio
docker-compose logs -f web          # Django
docker-compose logs -f postgres     # Base de datos
docker-compose logs -f redis        # Cache

# Ejecutar migraciones
docker-compose exec web python manage.py migrate

# Django shell
docker-compose exec web python manage.py shell

# Parar servicios
docker-compose down

# Parar y limpiar todo (incluyendo datos)
docker-compose down -v
```

### 5. Servicios Incluidos
| Servicio | Puerto | URL |
|----------|--------|-----|
| Django API | 8000 | http://localhost:8000 |
| PostgreSQL | 5432 | postgres://localhost:5432 |
| Redis | 6379 | redis://localhost:6379 |
| Celery Worker | - | - |
| Celery Beat | - | - |

Para más detalles ver `DOCKER_SETUP.md`

---

## Testing

### Tests de Flujos (Flujo Estudiante y Profesor)

Los tests de flujos validan los procesos principales del sistema:

```bash
# Ver todos los tests
pytest tests_flujos.py -v

# Resumen rápido
pytest tests_flujos.py -q

# Solo flujo estudiante
pytest tests_flujos.py::TestFlujoEstudiante -v

# Solo flujo profesor
pytest tests_flujos.py::TestFlujoProfesor -v

# Solo flujos integrados
pytest tests_flujos.py::TestFlujoIntegrado -v

# Con Docker
docker-compose exec web pytest tests_flujos.py -v
```

Resultados:

```
16/16 TESTS PASSING (100%)

TestFlujoEstudiante (7 tests)
- test_11_login_estudiante
- test_12_inscribirse_en_materia
- test_13_ver_materias_inscritas
- test_14_ver_materias_aprobadas
- test_15_ver_materias_reprobadas
- test_16_ver_promedio_gpa
- test_17_ver_historico_academico

TestFlujoProfesor (6 tests)
- test_18_login_profesor
- test_19_ver_materias_asignadas
- test_20_ver_estudiantes_por_materia
- test_21_calificar_estudiante
- test_22_finalizar_materia
- test_materias_anteriores_y_promedios

TestFlujoIntegrado (3 tests)
- test_flujo_completo_inscripcion_y_calificacion
- test_flujo_estudiante_ve_gpa_actualizado
- test_profesor_no_puede_cerrar_con_estudiantes_sin_calificar

Coverage: 34%
```

### Tests Críticos (Endpoints específicos)

```bash
pytest tests_critical_endpoints.py -v
```

## Endpoints Principales

Los 5 endpoints más importantes del sistema:

1. POST /api/auth/token/ - Obtener token JWT para autenticación
   ```bash
   curl -X POST http://localhost:8000/api/auth/token/ \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "admin123"}'
   ```

2. POST /api/subjects/student/enroll/ - Inscribir estudiante en materia
   Permite que un estudiante se inscriba en una materia disponible.

3. POST /api/subjects/instructor/grade/ - Asignar calificación a estudiante
   El profesor asigna una calificación a un estudiante inscrito (0.0 a 5.0).

4. GET /api/subjects/student/gpa/ - Obtener promedio general del estudiante
   Retorna el GPA (promedio de todas las calificaciones) del estudiante autenticado.

5. GET /api/accounts/statistics/ - Ver estadísticas del sistema
   Solo administrador. Retorna estadísticas completas de usuarios, materias, inscripciones.

---

## Otros Endpoints Disponibles

Autenticación:
- POST /api/auth/token/ - Obtener JWT token
- POST /api/auth/refresh/ - Refrescar token

Gestión de Usuarios (Admin):
- POST /api/accounts/create_user/ - Crear usuario
- POST /api/accounts/{id}/assign_role/ - Asignar rol
- POST /api/accounts/{id}/change_role/ - Cambiar rol
- GET /api/accounts/ - Listar usuarios
- GET /api/accounts/statistics/ - Ver estadísticas

Gestión de Materias (Admin):
- POST /api/subjects/ - Crear materia
- GET /api/subjects/ - Listar materias
- POST /api/subjects/{id}/assign_instructor/ - Asignar profesor

Flujo Estudiante:
- POST /api/subjects/student/enroll/ - Inscribirse
- GET /api/subjects/student/enrolled/ - Materias inscritas
- GET /api/subjects/student/approved/ - Materias aprobadas
- GET /api/subjects/student/failed/ - Materias reprobadas
- GET /api/subjects/student/gpa/ - Promedio general
- GET /api/subjects/student/history/ - Histórico completo

Flujo Profesor:
- GET /api/subjects/instructor/assigned_subjects/ - Mis materias
- GET /api/subjects/instructor/students/?subject_id=X - Estudiantes
- POST /api/subjects/instructor/grade/ - Calificar estudiante
- POST /api/subjects/instructor/close/ - Cerrar materia

Reportes:
- GET /api/reports/student/{id}/ - Reporte estudiante (CSV)
- GET /api/reports/instructor/{id}/ - Reporte instructor (CSV)

Notificaciones:
- GET /api/notifications/ - Listar notificaciones
- GET /api/notifications/{id}/ - Detalle de notificación

## Documentación

API Documentation (Swagger):
http://localhost:8000/swagger/

API Documentation (ReDoc):
http://localhost:8000/redoc/

Para más detalles ver:
- TESTING_GUIDE.md - Ejemplos de uso de todos los endpoints
- DOCKER_SETUP.md - Guía completa de Docker
- DOCKER_QUICK_START.md - Quick start con Docker

## Credenciales de Prueba

Admin:
- Username: admin
- Password: admin123

Instructor:
- Username: instructor
- Password: instructor123

Student:
- Username: student
- Password: student123

## Requisitos

- Python 3.12+
- Django 5.0.6
- Django REST Framework 3.15.2
- PostgreSQL (en producción) / SQLite (desarrollo)
- Redis (para Celery)

## Stack Tecnológico

Backend:
- Django 5.0.6
- Django REST Framework 3.15.2
- djangorestframework-simplejwt (autenticación JWT)
- celery (tareas asincrónicas)
- django-celery-beat (tareas programadas)

Base de Datos:
- PostgreSQL (producción)
- SQLite (desarrollo/testing)

Cache:
- Redis

Testing:
- pytest
- pytest-django
- pytest-cov

Docker:
- Docker
- Docker Compose

## Licencia

Este proyecto es parte de una prueba técnica de backend con Django.

---

Última actualización: 2025-10-22
Versión: 1.0 con tests de flujos completados
Status: Listo para usar
