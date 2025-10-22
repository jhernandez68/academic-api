"""
Vistas para gestión de materias e inscripciones académicas.

Este módulo proporciona endpoints REST para:
- CRUD de materias (solo administradores)
- Asignación de instructores a materias
- Inscripción de estudiantes en materias
- Consultas de historial académico de estudiantes
- Asignación de calificaciones por instructores
- Cierre de materias después de calificar
"""

from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from common.permissions import IsAdmin, IsInstructor, IsStudent
from common.decorators import validate_prerequisites
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Subject, Enrollment
from .serializers import SubjectSerializer, EnrollmentSerializer, AssignInstructorSerializer
from . import services

class SubjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de materias del programa académico.

    Endpoints:
        GET /subjects/ - Listar todas las materias (requiere autenticación)
        GET /subjects/{id}/ - Obtener detalle de una materia (requiere autenticación)
        POST /subjects/ - Crear nueva materia (requiere rol admin)
        PUT /subjects/{id}/ - Actualizar materia completa (requiere rol admin)
        PATCH /subjects/{id}/ - Actualizar materia parcial (requiere rol admin)
        DELETE /subjects/{id}/ - Eliminar materia (requiere rol admin)
        POST /subjects/{id}/assign_instructor/ - Asignar profesor a materia (requiere rol admin)

    Permisos:
        - Listar y obtener: Requiere autenticación básica
        - CRUD y assign_instructor: Requiere rol administrador
    """
    queryset = Subject.objects.all().order_by("id")
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Determina permisos según la acción realizada."""
        if self.action in ["create","update","partial_update","destroy","assign_instructor"]:
            return [IsAdmin()]
        return [IsAuthenticated()]

    @swagger_auto_schema(request_body=AssignInstructorSerializer, responses={200: SubjectSerializer})
    @action(detail=True, methods=["post"])
    def assign_instructor(self, request, pk=None):
        """
        Asigna un profesor a una materia.

        Args:
            request: Solicitud HTTP con datos en el body:
                - instructor_user_id (int): ID del usuario con rol 'instructor'
            pk: ID de la materia

        Returns:
            Response: Objeto de la materia actualizada con el instructor asignado

        Raises:
            Http404: Si la materia no existe
            Http404: Si el usuario no existe o no tiene rol 'instructor'
        """
        s = services.assign_instructor(pk, request.data.get("instructor_user_id"))
        return Response(SubjectSerializer(s).data)

class StudentViewSet(viewsets.GenericViewSet):
    """
    ViewSet para gestión de inscripciones de estudiantes.

    Endpoints:
        POST /students/enroll/ - Inscribir estudiante en materia
        GET /students/enrolled/ - Obtener materias cursando actualmente
        GET /students/approved/ - Obtener materias aprobadas
        GET /students/failed/ - Obtener materias reprobadas
        GET /students/gpa/ - Obtener promedio general del estudiante
        GET /students/history/ - Obtener historial completo de inscripciones

    Restricción de permisos:
        - Todos los endpoints requieren autenticación y rol 'student'
        - Cada estudiante solo puede acceder a sus propios datos
    """
    serializer_class = EnrollmentSerializer
    queryset = Enrollment.objects.all()
    permission_classes = [IsAuthenticated, IsStudent]

    @action(detail=False, methods=["post"])
    @validate_prerequisites
    def enroll(self, request):
        """
        Inscribe al estudiante en una materia.

        Args:
            request: Solicitud HTTP con datos en el body:
                - subject_id (int): ID de la materia en la que inscribirse

        Returns:
            Response: Diccionario con el ID de la inscripción creada y status HTTP 201

        Validaciones realizadas (mediante decorator @validate_prerequisites):
            1. Usuario debe tener rol 'student'
            2. No puede estar ya inscrito o haber aprobado la materia
            3. Debe cumplir con todos los prerrequisitos
            4. No puede exceder el máximo de créditos permitidos

        Raises:
            Http400: Si falla alguna validación, retorna mensaje descriptivo del error
        """
        e = services.enroll(request.user, request.data.get("subject_id"))
        return Response({"id": e.id}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def enrolled(self, request):
        """
        Obtiene todas las materias actualmente cursando.

        Args:
            request: Solicitud HTTP (solo requiere autenticación)

        Returns:
            Response: Lista de inscripciones en estado 'enrolled' con detalles de materia
        """
        qs = services.enrolled_subjects(request.user)
        return Response(EnrollmentSerializer(qs, many=True).data)

    @action(detail=False, methods=["get"])
    def approved(self, request):
        """
        Obtiene todas las materias aprobadas.

        Materias aprobadas son aquellas con calificación >= 3.0

        Args:
            request: Solicitud HTTP (solo requiere autenticación)

        Returns:
            Response: Lista de inscripciones en estado 'approved' ordenadas por fecha
        """
        qs = services.approved_subjects(request.user)
        return Response(EnrollmentSerializer(qs, many=True).data)

    @action(detail=False, methods=["get"])
    def failed(self, request):
        """
        Obtiene todas las materias reprobadas.

        Materias reprobadas son aquellas con calificación < 3.0

        Args:
            request: Solicitud HTTP (solo requiere autenticación)

        Returns:
            Response: Lista de inscripciones en estado 'failed'
        """
        qs = services.failed_subjects(request.user)
        return Response(EnrollmentSerializer(qs, many=True).data)

    @action(detail=False, methods=["get"])
    def gpa(self, request):
        """
        Calcula y retorna el promedio general (GPA) del estudiante.

        Cálculo:
            - Promedio de todas las materias que tienen calificación asignada
            - Retorna 0.0 si no hay materias calificadas

        Args:
            request: Solicitud HTTP (solo requiere autenticación)

        Returns:
            Response: Diccionario con la clave 'gpa' (número decimal 0.0 a 5.0)
        """
        v = services.gpa(request.user)
        return Response({"gpa": float(v)})

    @action(detail=False, methods=["get"])
    def history(self, request):
        """
        Obtiene el historial completo de inscripciones del estudiante.

        Historial incluye todas las inscripciones desde que el estudiante se registró,
        sin importar su estado actual (enrolled, approved, failed, closed).

        Args:
            request: Solicitud HTTP (solo requiere autenticación)

        Returns:
            Response: Lista de todas las inscripciones ordenadas por fecha de creación
        """
        qs = services.history(request.user)
        return Response(EnrollmentSerializer(qs, many=True).data)

class InstructorViewSet(viewsets.GenericViewSet):
    """
    ViewSet para gestión de inscripciones desde la perspectiva del instructor.

    Endpoints:
        GET /instructors/assigned_subjects/ - Obtener materias asignadas
        GET /instructors/students/?subject_id=X - Obtener estudiantes de una materia
        POST /instructors/grade/ - Asignar calificación a estudiante
        POST /instructors/close/ - Cerrar materia después de calificar todos

    Restricción de permisos:
        - Todos los endpoints requieren autenticación y rol 'instructor'
        - Los instructores solo pueden ver y calificar a sus propios estudiantes
    """
    serializer_class = EnrollmentSerializer
    queryset = Enrollment.objects.all()
    permission_classes = [IsAuthenticated, IsInstructor]

    @action(detail=False, methods=["get"])
    def assigned_subjects(self, request):
        """
        Obtiene todas las materias asignadas al instructor.

        Args:
            request: Solicitud HTTP (solo requiere autenticación)

        Returns:
            Response: Lista de materias donde el instructor es assigned_instructor
        """
        qs = Subject.objects.filter(assigned_instructor=request.user)
        return Response(SubjectSerializer(qs, many=True).data)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('subject_id', openapi.IN_QUERY, description="ID de la materia", type=openapi.TYPE_INTEGER, required=True)
        ],
        responses={200: EnrollmentSerializer(many=True)}
    )
    @action(detail=False, methods=["get"])
    def students(self, request):
        """
        Obtiene todos los estudiantes inscritos en una materia específica del instructor.

        Args:
            request: Solicitud HTTP con parámetro de query:
                - subject_id (int, requerido): ID de la materia

        Returns:
            Response: Lista de inscripciones de estudiantes en esa materia

        Validación:
            - Solo retorna estudiantes de materias asignadas a este instructor
        """
        subject_id = request.query_params.get("subject_id")
        qs = services.students_by_subject(request.user, subject_id)
        return Response(EnrollmentSerializer(qs, many=True).data)

    @action(detail=False, methods=["post"])
    def grade(self, request):
        """
        Asigna una calificación a un estudiante en una materia.

        Args:
            request: Solicitud HTTP con datos en el body:
                - enrollment_id (int): ID de la inscripción a calificar
                - value (float): Calificación entre 0.0 y 5.0

        Returns:
            Response: Objeto de inscripción actualizado con la calificación y estado

        Comportamiento:
            - Calificación >= 3.0: estado cambia a 'approved'
            - Calificación < 3.0: estado cambia a 'failed'
            - Se crea automáticamente una notificación para el estudiante
            - Redondea la calificación a 1 decimal

        Validaciones:
            - La calificación debe estar entre 0.0 y 5.0
            - La inscripción debe pertenecer a una materia asignada al instructor
            - Solo el instructor asignado puede calificar

        Raises:
            Http400: Si la calificación está fuera del rango
            Http404: Si la inscripción no existe o no pertenece a este instructor
        """
        try:
            enrollment_id = request.data.get("enrollment_id")
            value = float(request.data.get("value"))

            if value < 0 or value > 5:
                return Response(
                    {"error": "La calificación debe estar entre 0.0 y 5.0"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            e = services.grade(request.user, enrollment_id, value)
            return Response(EnrollmentSerializer(e).data)
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=["post"])
    def close(self, request):
        """
        Cierra una materia después de que todos los estudiantes han sido calificados.

        Args:
            request: Solicitud HTTP con datos en el body:
                - subject_id (int): ID de la materia a cerrar

        Returns:
            Response: Diccionario con clave 'closed' (bool):
                - True: si se cerró exitosamente
                - False: si falló (materia sin inscritos, hay estudiantes sin calificar, etc.)

        Precondiciones:
            - Todos los estudiantes inscritos deben tener una calificación asignada
            - El instructor debe ser el profesor asignado a la materia

        Efecto:
            - Cambia el estado de todas las inscripciones de la materia a 'closed'
        """
        subject_id = request.data.get("subject_id")
        ok = services.close_subject(request.user, subject_id)
        return Response({"closed": ok})
