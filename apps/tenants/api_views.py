from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from .models import Tenant, TenantUser
from .serializers import TenantSerializer, TenantDashboardSerializer

class TenantDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get the first tenant where this user is an admin or staff
        tenant_user = TenantUser.objects.filter(user=request.user).first()
        
        if not tenant_user:
            return Response({"error": "No tenant associated with this user"}, status=status.HTTP_404_NOT_FOUND)
            
        tenant = tenant_user.tenant
        
        # Mocking some stats for now
        data = {
            "business_name": tenant.name,
            "subdomain": tenant.subdomain,
            "business_type": tenant.get_business_type_display(),
            "total_products": 0, # To be linked later
            "total_staff": tenant.users.count()
        }
        
        serializer = TenantDashboardSerializer(data)
        return Response(serializer.data)

class TenantListCreateAPIView(generics.ListCreateAPIView):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated] # Or a custom IsPlatformAdmin permission
