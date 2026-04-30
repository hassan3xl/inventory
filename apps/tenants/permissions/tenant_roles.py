from rest_framework import permissions
from apps.tenants.models import TenantUser

class HasTenantAccess(permissions.BasePermission):
    """
    Base permission for any user belonging to the current tenant.
    """
    message = "You do not have access to this business context."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            self.message = "Authentication required."
            return False
            
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            self.message = "Tenant context missing. Please access via your business subdomain."
            return False

        # Get user's relationship with this tenant
        try:
            request.tenant_user = TenantUser.objects.get(user=request.user, tenant=tenant)
            return True
        except TenantUser.DoesNotExist:
            self.message = f"You are not a registered staff member of '{tenant.name}'."
            return False

class IsTenantAdmin(HasTenantAccess):
    """
    Allows access only to Tenant Administrators.
    """
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        
        return request.tenant_user.role == TenantUser.Role.ADMIN

class IsTenantManager(HasTenantAccess):
    """
    Allows access to Managers and Admins.
    """
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        
        return request.tenant_user.role in [TenantUser.Role.ADMIN, TenantUser.Role.MANAGER]

class IsTenantStaff(HasTenantAccess):
    """
    Allows access to any staff member (Admin, Manager, or Staff).
    """
    def has_permission(self, request, view):
        return super().has_permission(request, view)
