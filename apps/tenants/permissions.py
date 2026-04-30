from rest_framework import permissions
from .models import TenantUser

class HasTenantAccess(permissions.BasePermission):
    """
    Allows access only to users who have a role in the current tenant.
    The tenant is identified by the TenantMiddleware (request.tenant).
    """
    message = "You do not have permission to access this business context."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            self.message = "Authentication required."
            return False
            
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            self.message = "Tenant context missing. Please access via your business subdomain."
            return False

        # Check if user has any role in this specific tenant
        has_access = TenantUser.objects.filter(user=request.user, tenant=tenant).exists()
        if not has_access:
            self.message = f"User {request.user.email} is not authorized for the business '{tenant.name}'."
        
        return has_access
