# 🧪 Guía de Prueba de Endpoints - Academic API

## 📋 Índice
1. [Autenticación](#autenticación)
2. [Gestión de Usuarios](#gestión-de-usuarios)
3. [Gestión de Materias](#gestión-de-materias)
4. [Flujo Estudiante](#flujo-estudiante)
5. [Flujo Profesor](#flujo-profesor)
6. [Reportes](#reportes)
7. [Notificaciones](#notificaciones)
8. [Estadísticas](#estadísticas)

---

## Autenticación

### 1. Login - Obtener Token JWT

**Endpoint:** `POST http://localhost:8000/api/auth/token/`

**Payload:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Respuesta esperada (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Guardar:** El valor de `access` para usarlo en los siguientes requests como `Authorization: Bearer {access_token}`

---

### 2. Refresh Token

**Endpoint:** `POST http://localhost:8000/api/auth/refresh/`

**Payload:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Respuesta esperada (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

## Gestión de Usuarios

### 3. Crear Usuario

**Endpoint:** `POST http://localhost:8000/api/accounts/create_user/`

**Headers:**
```
Authorization: Bearer {admin_access_token}
Content-Type: application/json
```

**Payload:**
```json
{
  "username": "estudiante1",
  "email": "estudiante1@test.com",
  "first_name": "Juan",
  "last_name": "Pérez",
  "password": "testpass123",
  "role": 3
}
```

**Notas:**
- `role`: ID del rol (1=admin, 2=instructor, 3=student)
- En este caso usamos 3 para crear un estudiante sin rol asignado (opcional)

**Respuesta esperada (201 Created):**
```json
{
  "id": 5,
  "username": "estudiante1",
  "email": "estudiante1@test.com",
  "first_name": "Juan",
  "last_name": "Pérez",
  "role": {
    "id": 3,
    "name": "student",
    "display_name": "Estudiante"
  }
}
```

**Guardar:** El `id` del usuario (ej: 5)

---

### 4. Asignar Rol (Primera vez)

**Endpoint:** `POST http://localhost:8000/api/accounts/{user_id}/assign_role/`

**Ejemplo:** `POST http://localhost:8000/api/accounts/5/assign_role/`

**Headers:**
```
Authorization: Bearer {admin_access_token}
Content-Type: application/json
```

**Payload:**
```json
{
  "role": "student"
}
```

**Respuesta esperada (200 OK):**
```json
{
  "id": 5,
  "username": "estudiante1",
  "email": "estudiante1@test.com",
  "first_name": "",
  "last_name": "",
  "role": {
    "id": 3,
    "name": "student",
    "display_name": "Estudiante"
  }
}
```

---

### 5. Cambiar Rol (Ya tiene rol)

**Endpoint:** `POST http://localhost:8000/api/accounts/{user_id}/change_role/`

**Ejemplo:** `POST http://localhost:8000/api/accounts/5/change_role/`

**Headers:**
```
Authorization: Bearer {admin_access_token}
Content-Type: application/json
```

**Payload:**
```json
{
  "role": "instructor"
}
```

**Respuesta esperada (200 OK):**
```json
{
  "id": 5,
  "username": "estudiante1",
  "email": "estudiante1@test.com",
  "first_name": "",
  "last_name": "",
  "role": {
    "id": 2,
    "name": "instructor",
    "display_name": "Instructor"
  }
}
```

---

### 6. Listar Usuarios

**Endpoint:** `GET http://localhost:8000/api/accounts/`

**Headers:**
```
Authorization: Bearer {admin_access_token}
```

**Respuesta esperada (200 OK):**
```json
[
  {
    "id": 1,
    "username": "admin1",
    "email": "admin1@test.com",
    "first_name": "",
    "last_name": "",
    "role": {
      "id": 1,
      "name": "admin",
      "display_name": "Administrador"
    }
  },
  ...
]
```

---

### 7. Obtener Usuario por ID

**Endpoint:** `GET http://localhost:8000/api/accounts/{user_id}/`

**Ejemplo:** `GET http://localhost:8000/api/accounts/5/`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Respuesta esperada (200 OK):**
```json
{
  "id": 5,
  "username": "estudiante1",
  "email": "estudiante1@test.com",
  "first_name": "",
  "last_name": "",
  "role": {
    "id": 3,
    "name": "student",
    "display_name": "Estudiante"
  }
}
```

---

## Gestión de Materias

### 8. Crear Materia

**Endpoint:** `POST http://localhost:8000/api/subjects/`

**Headers:**
```
Authorization: Bearer {admin_access_token}
Content-Type: application/json
```

**Payload:**
```json
{
  "name": "Matemáticas Avanzada",
  "code": "MAT101",
  "credits": 4,
  "semester": 1
}
```

**Respuesta esperada (201 Created):**
```json
{
  "id": 1,
  "name": "Matemáticas Avanzada",
  "code": "MAT101",
  "credits": 4,
  "semester": 1,
  "assigned_instructor": null,
  "prerequisites": []
}
```

**Guardar:** El `id` de la materia (ej: 1)

---

### 9. Listar Materias

**Endpoint:** `GET http://localhost:8000/api/subjects/`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Respuesta esperada (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Matemáticas Avanzada",
    "code": "MAT101",
    "credits": 4,
    "semester": 1,
    "assigned_instructor": null,
    "prerequisites": []
  },
  ...
]
```

---

### 10. Asignar Profesor a Materia

**Endpoint:** `POST http://localhost:8000/api/subjects/{subject_id}/assign_instructor/`

**Ejemplo:** `POST http://localhost:8000/api/subjects/1/assign_instructor/`

**Headers:**
```
Authorization: Bearer {admin_access_token}
Content-Type: application/json
```

**Payload:**
```json
{
  "instructor_user_id": 4
}
```

**Notas:**
- `instructor_user_id`: ID del usuario que tiene rol "instructor"
- En este ejemplo usamos el usuario con ID 4 (profesor1)

**Respuesta esperada (200 OK):**
```json
{
  "id": 1,
  "name": "Matemáticas Avanzada",
  "code": "MAT101",
  "credits": 4,
  "semester": 1,
  "assigned_instructor": {
    "id": 4,
    "username": "profesor1",
    "email": "profesor1@test.com",
    "first_name": "",
    "last_name": "",
    "role": {
      "id": 2,
      "name": "instructor",
      "display_name": "Instructor"
    }
  },
  "prerequisites": []
}
```

---

## Flujo Estudiante

### 11. Login como Estudiante

**Endpoint:** `POST http://localhost:8000/api/auth/token/`

**Payload:**
```json
{
  "username": "student",
  "password": "student123"
}
```

**Guardar:** El `access` token del estudiante

---

### 12. Inscribirse en Materia

**Endpoint:** `POST http://localhost:8000/api/subjects/student/enroll/`

**Headers:**
```
Authorization: Bearer {student_access_token}
Content-Type: application/json
```

**Payload:**
```json
{
  "subject_id": 1
}
```

**Respuesta esperada (201 Created):**
```json
{
  "id": 10
}
```

---

### 13. Ver Materias Inscritas

**Endpoint:** `GET http://localhost:8000/api/subjects/student/enrolled/`

**Headers:**
```
Authorization: Bearer {student_access_token}
```

**Respuesta esperada (200 OK):**
```json
[
  {
    "id": 1,
    "student": 3,
    "subject": {
      "id": 1,
      "name": "Programación I",
      "code": "PRO101",
      "credits": 3,
      "assigned_instructor": {...},
      "prerequisites": []
    },
    "state": "enrolled",
    "grade": null,
    "created_at": "2025-10-21T12:30:00Z"
  }
]
```

**Nota:** El estudiante seed (`student`) tiene 1 materia inscrita sin calificación

---

### 14. Ver Materias Aprobadas

**Endpoint:** `GET http://localhost:8000/api/subjects/student/approved/`

**Headers:**
```
Authorization: Bearer {student_access_token}
```

**Respuesta esperada (200 OK):**
```json
[
  {
    "id": 2,
    "student": 3,
    "subject": {
      "id": 2,
      "name": "Bases de Datos I",
      "code": "BDD101",
      "credits": 4,
      "assigned_instructor": {...},
      "prerequisites": []
    },
    "state": "approved",
    "grade": 4.5,
    "created_at": "2025-10-21T12:30:00Z"
  },
  {
    "id": 3,
    "student": 3,
    "subject": {
      "id": 7,
      "name": "Sistemas Operativos",
      "code": "SO101",
      "credits": 3,
      "assigned_instructor": {...},
      "prerequisites": []
    },
    "state": "approved",
    "grade": 4.0,
    "created_at": "2025-10-21T12:30:00Z"
  }
]
```

**Nota:** El estudiante seed tiene 2 materias aprobadas con calificaciones

---

### 15. Ver Materias Reprobadas

**Endpoint:** `GET http://localhost:8000/api/subjects/student/failed/`

**Headers:**
```
Authorization: Bearer {student_access_token}
```

**Respuesta esperada (200 OK):**
```json
[]
```

**Nota:** El estudiante seed no tiene materias reprobadas

---

### 16. Ver Promedio General (GPA)

**Endpoint:** `GET http://localhost:8000/api/subjects/student/gpa/`

**Headers:**
```
Authorization: Bearer {student_access_token}
```

**Respuesta esperada (200 OK):**
```json
{
  "gpa": 4.25
}
```

**Nota:** Promedio de 2 materias aprobadas: (4.5 + 4.0) / 2 = 4.25

---

### 17. Ver Histórico Académico

**Endpoint:** `GET http://localhost:8000/api/subjects/student/history/`

**Headers:**
```
Authorization: Bearer {student_access_token}
```

**Respuesta esperada (200 OK):**
```json
[
  {
    "id": 1,
    "student": 3,
    "subject": {
      "id": 1,
      "name": "Programación I",
      "code": "PRO101",
      "credits": 3,
      "assigned_instructor": {...},
      "prerequisites": []
    },
    "state": "enrolled",
    "grade": null,
    "created_at": "2025-10-21T12:30:00Z"
  },
  {
    "id": 2,
    "student": 3,
    "subject": {
      "id": 2,
      "name": "Bases de Datos I",
      "code": "BDD101",
      "credits": 4,
      "assigned_instructor": {...},
      "prerequisites": []
    },
    "state": "approved",
    "grade": 4.5,
    "created_at": "2025-10-21T12:30:00Z"
  },
  {
    "id": 3,
    "student": 3,
    "subject": {
      "id": 7,
      "name": "Sistemas Operativos",
      "code": "SO101",
      "credits": 3,
      "assigned_instructor": {...},
      "prerequisites": []
    },
    "state": "approved",
    "grade": 4.0,
    "created_at": "2025-10-21T12:30:00Z"
  }
]
```

**Nota:** Incluye todas las materias (inscritas, aprobadas, reprobadas)

---

## Flujo Profesor

### 18. Login como Profesor

**Endpoint:** `POST http://localhost:8000/api/auth/token/`

**Payload:**
```json
{
  "username": "instructor",
  "password": "instructor123"
}
```

**Guardar:** El `access` token del profesor

---

### 19. Ver Materias Asignadas

**Endpoint:** `GET http://localhost:8000/api/subjects/instructor/assigned_subjects/`

**Headers:**
```
Authorization: Bearer {instructor_access_token}
```

**Respuesta esperada (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Matemáticas Avanzada",
    "code": "MAT101",
    "credits": 4,
    "semester": 1,
    "assigned_instructor": {...},
    "prerequisites": []
  }
]
```

---

### 20. Ver Estudiantes por Materia

**Endpoint:** `GET http://localhost:8000/api/subjects/instructor/students/?subject_id=1`

**Headers:**
```
Authorization: Bearer {instructor_access_token}
```

**Respuesta esperada (200 OK):**
```json
[
  {
    "id": 10,
    "student": 5,
    "subject": 1,
    "state": "enrolled",
    "grade": null,
    "created_at": "2025-10-21T12:30:00Z"
  }
]
```

---

### 21. Calificar Estudiante

**Endpoint:** `POST http://localhost:8000/api/subjects/instructor/grade/`

**Headers:**
```
Authorization: Bearer {instructor_access_token}
Content-Type: application/json
```

**Payload:**
```json
{
  "enrollment_id": 7,
  "value": 4.5
}
```

**Respuesta esperada (200 OK):**
```json
{
  "id": 10,
  "student": 5,
  "subject": 1,
  "state": "approved",
  "grade": 4.5,
  "created_at": "2025-10-21T12:30:00Z"
}
```

---

### 22. Finalizar Materia

**Endpoint:** `POST http://localhost:8000/api/subjects/instructor/close/`

**Headers:**
```
Authorization: Bearer {instructor_access_token}
Content-Type: application/json
```

**Payload:**
```json
{
  "subject_id": 1
}
```

**Respuesta esperada (200 OK):**
```json
{
  "closed": true
}
```

---

## Reportes

### 23. Descargar Reporte Estudiante (CSV)

**Endpoint:** `GET http://localhost:8000/api/reports/student/{student_id}/`

**Ejemplo:** `GET http://localhost:8000/api/reports/student/5/`

**Headers:**
```
Authorization: Bearer {admin_access_token}
```

**Respuesta (200 OK):** Archivo CSV descargado

```csv
Name,Subject,Grade,State
estudiante1,Matemáticas Avanzada,4.5,approved
```

---

### 24. Descargar Reporte Profesor (CSV)

**Endpoint:** `GET http://localhost:8000/api/reports/instructor/{instructor_id}/`

**Ejemplo:** `GET http://localhost:8000/api/reports/instructor/4/`

**Headers:**
```
Authorization: Bearer {admin_access_token}
```

**Respuesta (200 OK):** Archivo CSV descargado

```csv
Name,Subject,Average
profesor1,Matemáticas Avanzada,4.5
```

---

## Notificaciones

### 25. Ver Notificaciones

**Endpoint:** `GET http://localhost:8000/api/notifications/`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Respuesta esperada (200 OK):**
```json
[
  {
    "id": 1,
    "user": 5,
    "type": "grade",
    "message": "Grade 4.5 in Matemáticas Avanzada",
    "created_at": "2025-10-21T12:30:00Z",
    "read": false
  }
]
```

---

### 26. Obtener Notificación por ID

**Endpoint:** `GET http://localhost:8000/api/notifications/{notification_id}/`

**Ejemplo:** `GET http://localhost:8000/api/notifications/1/`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Respuesta esperada (200 OK):**
```json
{
  "id": 1,
  "user": 5,
  "type": "grade",
  "message": "Grade 4.5 in Matemáticas Avanzada",
  "created_at": "2025-10-21T12:30:00Z",
  "read": false
}
```

---

## Estadísticas

### 27. Ver Estadísticas del Sistema

**Endpoint:** `GET http://localhost:8000/api/accounts/statistics/`

**Headers:**
```
Authorization: Bearer {admin_access_token}
```

**Respuesta esperada (200 OK):**
```json
{
  "users": {
    "total_students": 15,
    "total_instructors": 5,
    "total_admins": 2,
    "active_students": 12,
    "inactive_students": 3
  },
  "subjects": {
    "total_subjects": 20,
    "subjects_with_instructor": 18,
    "subjects_without_instructor": 2,
    "avg_subjects_per_instructor": 3.6
  },
  "enrollments": {
    "total_enrollments": 45,
    "enrollments_enrolled": 20,
    "enrollments_approved": 18,
    "enrollments_failed": 5,
    "enrollments_closed": 2
  },
  "academic_performance": {
    "approval_rate": 78.26,
    "failure_rate": 21.74,
    "system_average_grade": 3.45,
    "average_student_gpa": 3.42
  },
  "grade_distribution": {
    "0_1": 2,
    "1_2": 3,
    "2_3": 8,
    "3_4": 15,
    "4_5": 12
  },
  "professors_with_assignments": 5
}
```

---

## 🔑 Credenciales de Prueba

```
ADMIN:
Username: admin1
Password: admin123

PROFESOR:
Username: profesor1
Password: testpass123

ESTUDIANTE:
Username: student1
Password: testpass123
```

---

## 📱 Herramientas Recomendadas

1. **Postman** - GUI para probar endpoints
2. **cURL** - Línea de comandos
3. **Thunder Client** (VSCode) - Extensión ligera
4. **Swagger UI** - Integrado en `/swagger/`

---

## ⚡ Acceso a Swagger

```
GET http://localhost:8000/swagger/
```

O

```
GET http://localhost:8000/redoc/
```

---

## 🚀 Flujo Rápido (5 Minutos)

Los datos semilla ya incluyen usuarios y materias con inscripciones reales:

1. **Autenticar como admin** (`admin`/`admin123`) → `/api/auth/token/`
2. **Ver usuarios** → `GET /api/accounts/`
3. **Ver materias** → `GET /api/subjects/`
4. **Autenticar como estudiante** (`student`/`student123`) → `/api/auth/token/`
5. **Ver materias inscritas** → `GET /api/subjects/student/enrolled/`
6. **Ver materias aprobadas** → `GET /api/subjects/student/approved/`
7. **Ver GPA** → `GET /api/subjects/student/gpa/`
8. **Autenticar como profesor** (`instructor`/`instructor123`) → `/api/auth/token/`
9. **Ver materias asignadas** → `GET /api/subjects/instructor/assigned_subjects/`
10. **Ver estudiantes** → `GET /api/subjects/instructor/students/?subject_id=1`
11. **Ver notificaciones** → `GET /api/notifications/`
12. **Ver estadísticas** → `GET /api/accounts/statistics/`

---

## 📝 Notas Importantes

- Todos los tokens JWT expiran en 30 minutos
- Usa el `refresh` token para obtener un nuevo `access` token
- Las operaciones sensibles requieren rol admin
- Los errores retornan en formato JSON con código HTTP apropiado
- Para cambiar de usuario, simplemente obtén un nuevo token con diferentes credenciales
