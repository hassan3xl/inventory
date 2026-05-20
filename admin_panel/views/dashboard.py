from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.tenants.models import Tenant


@login_required(login_url='/auth/login/')
def dashboard_view(request):
    total_tenants = Tenant.objects.count()
    active_tenants = Tenant.objects.filter(is_active=True).count()
    recent_tenants = Tenant.objects.order_by('-created_at')[:5]

    context = {
        'total_tenants': total_tenants,
        'active_tenants': active_tenants,
        'recent_tenants': recent_tenants,
    }
    return render(request, 'dashboard/index.html', context)
