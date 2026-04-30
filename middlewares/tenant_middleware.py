from django.shortcuts import get_object_or_404
from apps.tenants.models import Tenant
from utils.tenant_context import set_current_tenant, clear_current_tenant

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0]  # Handle port if present
        host_parts = host.split('.')
        
        # Assume subdomain is the first part: subdomain.myapp.com
        # In production, you'd check against a list of main domains
        # For local dev, we check if there are more than 2 parts (e.g., marcus.localhost)
        # 1. Try Subdomain
        subdomain = None
        if len(host_parts) > 2:
            subdomain = host_parts[0]
        elif len(host_parts) == 2 and host_parts[1] == 'localhost':
             subdomain = host_parts[0]

        # 2. Try X-Tenant Header (Best for development/Postman)
        tenant_slug = subdomain or request.headers.get('X-Tenant')

        if tenant_slug:
            try:
                tenant = Tenant.objects.get(subdomain=tenant_slug, is_active=True)
                request.tenant = tenant
                set_current_tenant(tenant)
            except Tenant.DoesNotExist:
                request.tenant = None
        else:
            request.tenant = None

        response = self.get_response(request)
        
        # Clean up after request
        clear_current_tenant()
        
        return response
