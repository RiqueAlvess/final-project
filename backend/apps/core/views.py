"""Core views - health check and tenant info."""

from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.tenants.serializers import TenantPublicSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint for Docker/load balancer."""
    return Response({'status': 'ok', 'schema': connection.schema_name})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tenant_info(request):
    """Return current tenant info based on the request domain."""
    tenant = request.tenant
    serializer = TenantPublicSerializer(tenant)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Return basic dashboard statistics for the current tenant."""
    from apps.users.models import User, UserRole

    total_users = User.objects.filter(is_active=True).count()
    rh_users = User.objects.filter(role=UserRole.RH, is_active=True).count()
    leader_users = User.objects.filter(role=UserRole.LEADER, is_active=True).count()
    locked_users = User.objects.filter(is_locked=True).count()

    return Response({
        'users': {
            'total': total_users,
            'rh': rh_users,
            'leaders': leader_users,
            'locked': locked_users,
        },
        'tenant': {
            'name': request.tenant.name,
            'schema': connection.schema_name,
        }
    })
