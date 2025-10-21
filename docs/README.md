# Documentación de Diseño de Base de Datos

## Diagrama Entidad-Relación (ERD)

Esta carpeta contiene la documentación del modelo de datos de la aplicación Academic API.

### 📊 Generar el Diagrama ERD

#### Opción 1: Usando DataFinz (Recomendado)

1. Ve a: **https://tryout.datafinz.com/tryERD**
2. Abre el archivo `erd.json` desde esta carpeta
3. Copia todo el contenido del archivo JSON
4. Pégalo en el editor de DataFinz
5. El diagrama se generará automáticamente
6. Descarga la imagen (PNG, SVG, etc.) desde DataFinz
7. Guarda la imagen en esta carpeta con el nombre `erd_diagram.png` o similar

#### Opción 2: Usando dbdiagram.io

1. Ve a: **https://dbdiagram.io/d**
2. Crea un nuevo proyecto
3. Importa o copia el contenido del `erd.json` (puede requerir ajustes de formato)
4. Descarga el diagrama

### 📁 Estructura de Carpetas

```
docs/
├── README.md          # Este archivo
├── erd.json           # Archivo JSON con la definición del modelo ER
└── erd_diagram.png    # Imagen del diagrama (generada después de exportar)
```

### 🗄️ Entidades Principales

| Tabla | Descripción | Relaciones Clave |
|-------|-------------|-----------------|
| **Role** | Define roles del sistema (admin, instructor, student) | 1:N → User |
| **User** | Usuario del sistema (base para estudiantes, profesores, etc.) | N:1 ← Role, 1:1 ← Student/Instructor, 1:N → Enrollment, 1:N → Notification |
| **Student** | Perfil extendido para estudiantes | 1:1 → User |
| **Instructor** | Perfil extendido para profesores | 1:1 → User |
| **Subject** | Materias/Asignaturas del sistema | 1:N → Enrollment, M:N ← Subject (prerequisites), N:1 ← User (assigned_instructor) |
| **Enrollment** | Inscripción de estudiantes en materias | N:1 → User, N:1 → Subject |
| **Notification** | Notificaciones del sistema | N:1 → User |

### 🔗 Relaciones de Base de Datos

#### One-to-Many (1:N)
- Role → User
- User → Student (instructor profile)
- User → Subject (assigned subjects)
- User → Enrollment (student enrollments)
- User → Notification
- Subject → Enrollment

#### One-to-One (1:1)
- User → Student
- User → Instructor

#### Many-to-Many (M:N)
- Subject ↔ Subject (prerequisites - self-referential)

### 📋 Campos Importantes

#### Role
- `id` (PK)
- `name` (UNIQUE) - admin, instructor, student
- `display_name`

#### User
- `id` (PK)
- `username` (UNIQUE)
- `email`
- `password` (hashed)
- `first_name`, `last_name`
- `role_id` (FK → Role)

#### Student
- `id` (PK)
- `user_id` (FK → User, UNIQUE, OneToOne)
- `max_credits_per_term` (default: 16)

#### Instructor
- `id` (PK)
- `user_id` (FK → User, UNIQUE, OneToOne)
- `max_credits_per_term` (default: 20)

#### Subject
- `id` (PK)
- `name`
- `code` (UNIQUE)
- `credits`
- `assigned_instructor_id` (FK → User, nullable)
- `prerequisites` (M2M → Subject)

#### Enrollment
- `id` (PK)
- `student_id` (FK → User)
- `subject_id` (FK → Subject)
- `state` (enrolled, approved, failed, closed)
- `grade` (DECIMAL(3,1), nullable)
- **UNIQUE CONSTRAINT:** (student_id, subject_id)

#### Notification
- `id` (PK)
- `user_id` (FK → User)
- `type`
- `message`
- `created` (TIMESTAMP)
- `read` (BOOLEAN, default: False)

### 🎯 Reglas de Negocio en la BD

1. **Un usuario solo puede tener un rol**: Relación 1:1 con Role
2. **Un estudiante está vinculado a un usuario**: Relación 1:1 (OneToOne)
3. **Un profesor está vinculado a un usuario**: Relación 1:1 (OneToOne)
4. **Un estudiante no puede inscribirse dos veces en la misma materia**: UNIQUE(student_id, subject_id)
5. **Las inscripciones se eliminan si se elimina el estudiante o la materia**: CASCADE
6. **Los prerrequisitos son relaciones entre materias**: Self-referential M:N

### 📝 Cómo Usar el JSON

El archivo `erd.json` está formateado para ser compatible con herramientas de modelado ER. Incluye:

- **Entidades (entities)**: Definición completa de tablas con tipos de datos
- **Relaciones (relationships)**: Conexiones entre tablas
- **Atributos**: Campos con tipos, restricciones y claves foráneas

---

**Última actualización:** Octubre 2025
