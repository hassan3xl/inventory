from rest_framework import viewsets
from apps.tenants.permissions.tenant_roles import HasTenantAccess, IsTenantCashier
from apps.sales.models import Sale
from .serializers import SaleSerializer

class SaleViewSet(viewsets.ModelViewSet):
    serializer_class = SaleSerializer
    permission_classes = [HasTenantAccess, IsTenantCashier]

    def get_queryset(self):
        # TenantBaseModel manager automatically filters, but we ensure strict filtering here
        return Sale.objects.filter(tenant=self.request.tenant)

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)
