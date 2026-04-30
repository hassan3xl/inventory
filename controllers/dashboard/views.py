from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from apps.tenants.models import Tenant, TenantUser
from apps.tenants.permissions import HasTenantAccess
from apps.tenants.serializers import TenantSerializer, TenantDashboardSerializer

class BusinessProfileAPIView(APIView):
    permission_classes = [IsAuthenticated, HasTenantAccess]

    def get(self, request):
        tenant = request.tenant
        return Response({
            "name": tenant.name,
            "subdomain": tenant.subdomain,
            "category": tenant.get_business_type_display(),
            "is_active": tenant.is_active,
            "created_at": tenant.created_at
        })

class StaffProfileAPIView(APIView):
    permission_classes = [IsAuthenticated, HasTenantAccess]

    def get(self, request):
        tenant = request.tenant
        tenant_user = TenantUser.objects.get(user=request.user, tenant=tenant)

        return Response({
            "email": request.user.email,
            "role": tenant_user.role,
            "role_display": tenant_user.get_role_display(),
            "joined_at": tenant_user.created_at
        })

class DashboardStatsAPIView(APIView):
    permission_classes = [IsAuthenticated, HasTenantAccess]

    def get(self, request):
        tenant = request.tenant
        
        return Response({
            "total_products": 0,
            "total_staff": tenant.users.count(),
            "recent_activity": []
        })
