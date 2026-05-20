from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.tenants.models import Tenant, TenantUser
from apps.users.models import User
import string
import random


@login_required(login_url='/auth/login/')
def tenant_list_view(request):
    tenants = Tenant.objects.all().order_by('-created_at')

    if request.method == 'POST':
        name = request.POST.get('name')
        business_type = request.POST.get('business_type', Tenant.BusinessType.GENERAL)
        admin_email = request.POST.get('admin_email')

        if name and admin_email:
            user, created = User.objects.get_or_create(email=admin_email)
            if created:
                password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
                user.set_password(password)
                user.save()
                messages.info(request, f"An email has been sent to {admin_email} with their temporary password: {password}")
            else:
                messages.info(request, f"User {admin_email} already exists and will be assigned as admin.")

            tenant = Tenant.objects.create(name=name, business_type=business_type)
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
    
    # Get owner user
    owner_rel = tenant.users.filter(role=TenantUser.Role.OWNER).first()
    owner_user = owner_rel.user if owner_rel else None
    
    return render(request, 'tenants/details.html', {
        'tenant': tenant,
        'tenant_users': tenant_users,
        'owner_user': owner_user
    })


@login_required(login_url='/auth/login/')
def tenant_approve_view(request, pk):
    if request.method == 'POST':
        tenant = get_object_or_404(Tenant, pk=pk)
        
        # Activate owner user
        owner_rel = tenant.users.filter(role=TenantUser.Role.OWNER).first()
        if owner_rel and owner_rel.user:
            user = owner_rel.user
            if not user.is_active:
                user.is_active = True
                user.save()
                messages.success(request, f"User account '{user.email}' activated successfully!")
            else:
                messages.info(request, f"User account '{user.email}' is already active.")
        else:
            messages.warning(request, "No owner user found to activate.")
            
        tenant.is_active = True
        tenant.save()
        messages.success(request, f"Tenant '{tenant.name}' registration approved and store activated successfully!")
        
    return redirect('tenant_detail', pk=pk)


@login_required(login_url='/auth/login/')
def tenant_toggle_status_view(request, pk):
    if request.method == 'POST':
        tenant = get_object_or_404(Tenant, pk=pk)
        tenant.is_active = not tenant.is_active
        tenant.save()
        
        status_str = "activated" if tenant.is_active else "suspended"
        messages.success(request, f"Tenant '{tenant.name}' has been {status_str} successfully.")
        
    return redirect('tenant_detail', pk=pk)
