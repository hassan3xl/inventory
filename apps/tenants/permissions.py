from rest_framework import permissions
from .models import TenantUser

class HasTenantAccess(permissions.BasePermission):
    """
    Allows access only to users who have a role in the current tenant.
    The tenant is identified by the TenantMiddleware (request.tenant).
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return False

        # Check if user has any role in this specific tenant
        return TenantUser.objects.filter(user=request.user, tenant=tenant).exists()
