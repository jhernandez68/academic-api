"""
Decoradores personalizados para validaciones de negocio.

Este módulo contiene decoradores que ejecutan lógica de negocio antes de
procesar las vistas, permitiendo reutilización y validaciones centralizadas.

Decoradores:
    - validate_prerequisites: Valida que un estudiante cumpla requisitos para inscribirse
"""

from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from subjects.services import can_enroll

def validate_prerequisites(fn):
    """
    Decorador que valida si un estudiante puede inscribirse en una materia.

    Propósito:
        Intercepción de solicitudes de inscripción para verificar que el estudiante
        cumpla con todos los requisitos antes de procesarla.

    Validaciones realizadas:
        1. El usuario debe tener rol 'student'
        2. No puede estar ya inscrito o haber aprobado la materia
        3. Debe cumplir con todos los prerrequisitos de la materia
        4. No puede exceder el máximo de créditos permitidos

    Uso:
        @action(detail=False, methods=["post"])
        @validate_prerequisites
        def enroll(self, request):
            # Este método solo se ejecuta si todas las validaciones pasan

    Comportamiento:
        - Si alguna validación falla: Retorna HTTP 400 con mensaje de error detallado
        - Si todas pasan: Ejecuta la función decorada normalmente

    Args:
        fn: Función vista que será decorada

    Returns:
        wrapper: Función decorada que realiza validaciones antes de ejecutar fn

    Respuesta de error:
        HTTP 400 con JSON:
            {
                "detail": "Mensaje explicativo de por qué falló la validación"
            }

        Mensajes posibles:
            - "not authorized": Usuario no tiene rol student
            - "already taken or enrolled": Ya está inscrito o aprobó la materia
            - "missing prerequisites": No cumple con los prerrequisitos
            - "credits exceeded": Excedería el máximo de créditos
            - "ok": Todas las validaciones pasaron
    """
    @wraps(fn)
    def wrapper(view, request, *args, **kwargs):
        subject_id = request.data.get("subject_id")
        ok, msg = can_enroll(request.user, subject_id)
        if not ok:
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)
        return fn(view, request, *args, **kwargs)
    return wrapper
