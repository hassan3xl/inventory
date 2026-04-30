from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.text import slugify
from .models import Tenant, TenantUser
from apps.users.models import User
import string
import random

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

@login_required(login_url='/auth/login/')
def tenant_list_view(request):
    tenants = Tenant.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        subdomain = request.POST.get('subdomain') or slugify(name)
        business_type = request.POST.get('business_type', Tenant.BusinessType.GENERAL)
        admin_email = request.POST.get('admin_email')
        
        if name and subdomain and admin_email:
            if Tenant.objects.filter(subdomain=subdomain).exists():
                messages.error(request, f"Subdomain '{subdomain}' is already taken.")
            else:
                # 1. Create or get User
                user, created = User.objects.get_or_create(email=admin_email)
                if created:
                    password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
                    user.set_password(password)
                    user.save()
                    # In a real app, send an email with the password here
                    messages.info(request, f"An email has been sent to {admin_email} with their temporary password: {password}")
                else:
                    messages.info(request, f"User {admin_email} already exists and will be assigned as admin.")
                
                # 2. Create Tenant
                tenant = Tenant.objects.create(name=name, subdomain=subdomain, business_type=business_type)
                
                # 3. Create Tenant Role
                TenantUser.objects.create(tenant=tenant, user=user, role=TenantUser.Role.ADMIN)
                
                messages.success(request, f"Tenant '{name}' registered successfully!")
        return redirect('tenant_list')
        
    return render(request, 'tenants/list.html', {
        'tenants': tenants,
        'business_types': Tenant.BusinessType.choices
    })

@login_required(login_url='/auth/login/')
def tenant_detail_view(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    tenant_users = tenant.users.all().select_related('user')
    return render(request, 'tenants/details.html', {
        'tenant': tenant,
        'tenant_users': tenant_users
    })
