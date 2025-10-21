from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from common.permissions import IsAdmin
from .models import User
from .serializers import UserSerializer, CreateUserSerializer, AdminStatisticsSerializer
from .services import assign_role, get_admin_statistics

class UserViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated, IsAdmin])
    def create_user(self, request):
        s = CreateUserSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        u = s.save()
        return Response(UserSerializer(u).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdmin])
    def assign_role(self, request, pk=None):
        role = request.data.get("role")
        u = assign_role(pk, role)
        return Response(UserSerializer(u).data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated, IsAdmin])
    def statistics(self, request):
        """
        Retorna estadísticas generales del sistema.
        Solo accesible para administradores.

        Incluye:
        - Cantidad de usuarios por rol
        - Información sobre materias
        - Estado de inscripciones
        - Desempeño académico general
        - Distribución de calificaciones
        """
        stats = get_admin_statistics()
        serializer = AdminStatisticsSerializer(stats)
        return Response(serializer.data)
