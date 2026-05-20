from django.shortcuts import get_object_or_404
from apps.tenants.models import Tenant, TenantUser
from utils.tenant_context import set_current_tenant, clear_current_tenant
from utils.subdomain_handler import subdomain_handler

class TenantMiddleware:
    """
    Middleware to handle multi-tenant context.
    
    Priority order:
    1. X-Tenant header (for API requests)
    2. Subdomain (if subdomain routing is enabled)
    3. User's associated tenant (if authenticated)
    4. None (no tenant context)
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = None
        
        # 1. Try X-Tenant Header (Best for development/Postman/API)
        tenant_slug = request.headers.get('X-Tenant')
        
        # 2. Try Subdomain if subdomain routing is enabled
        if not tenant_slug and subdomain_handler.config.get('enabled'):
            host = request.get_host()
            subdomain = subdomain_handler.get_subdomain_from_host(host)
            if subdomain:
                tenant_slug = subdomain
        
        # 3. Try to get tenant from subdomain/header
        if tenant_slug:
            try:
                tenant = Tenant.objects.get(subdomain=tenant_slug, is_active=True)
            except Tenant.DoesNotExist:
                pass
        
        # 4. If no tenant from headers/subdomain but user is authenticated, get user's default tenant
        if not tenant and hasattr(request, 'user') and request.user and request.user.is_authenticated:
            try:
                tenant_user = TenantUser.objects.filter(user=request.user).first()
                if tenant_user:
                    tenant = tenant_user.tenant
            except Exception:
                pass
        
        request.tenant = tenant
        if tenant:
            set_current_tenant(tenant)

        response = self.get_response(request)
        
        # Clean up after request
        clear_current_tenant()
        
        return response
