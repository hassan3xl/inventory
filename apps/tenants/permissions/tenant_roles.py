from rest_framework import permissions
from apps.tenants.models import TenantUser
from utils.tenant_context import set_current_tenant


def resolve_tenant_for_user(request):
    """
    Attempt to resolve a tenant from the authenticated user.
    Used as a fallback when the middleware couldn't resolve it
    (e.g. because JWT auth runs after TenantMiddleware).
    """
    if not request.user or not request.user.is_authenticated:
        return None
    tenant_user = TenantUser.objects.filter(user=request.user).select_related('tenant').first()
    return tenant_user.tenant if tenant_user else None


class HasTenantAccess(permissions.BasePermission):
    """
    Base permission: the request's user belongs to the current tenant
    (any in-store role).
    """
    message = "You do not have access to this business context."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            self.message = "Authentication required."
            return False

        tenant = getattr(request, 'tenant', None)

        # Fallback: JWT auth resolves after TenantMiddleware, so try again now.
        if not tenant:
            tenant = resolve_tenant_for_user(request)
            if tenant:
                request.tenant = tenant
                set_current_tenant(tenant)

        if not tenant:
            self.message = (
                "Tenant context missing. "
                "Send an 'X-Tenant: <your-subdomain>' header or access via your business subdomain."
            )
            return False

        try:
            request.tenant_user = TenantUser.objects.get(user=request.user, tenant=tenant)
            return True
        except TenantUser.DoesNotExist:
            self.message = f"You are not a registered member of '{tenant.name}'."
            return False


class _RequiresMinRole(HasTenantAccess):
    """Internal base that checks a minimum role rank."""
    minimum_role = TenantUser.Role.STAFF

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if not request.tenant_user.has_role_at_least(self.minimum_role):
            self.message = (
                f"Your role '{request.tenant_user.get_role_display()}' does not have "
                f"permission for this action."
            )
            return False
        return True


class IsTenantOwner(_RequiresMinRole):
    """Store Owner only."""
    minimum_role = TenantUser.Role.OWNER


class IsTenantAdmin(_RequiresMinRole):
    """Administrator or above (Owner + Admin)."""
    minimum_role = TenantUser.Role.ADMIN


class IsTenantManager(_RequiresMinRole):
    """Manager or above (Owner, Admin, Manager)."""
    minimum_role = TenantUser.Role.MANAGER


class IsTenantCashier(_RequiresMinRole):
    """Cashier or above."""
    minimum_role = TenantUser.Role.CASHIER


class IsTenantStaff(HasTenantAccess):
    """Any staff member (all roles)."""
    pass
