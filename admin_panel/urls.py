from django.urls import path
from admin_panel.views.auth import login_view, register_view, logout_view
from admin_panel.views.dashboard import dashboard_view
from admin_panel.views.tenants import (
    tenant_list_view, 
    tenant_detail_view, 
    tenant_approve_view, 
    tenant_toggle_status_view
)

urlpatterns = [
    # Auth
    path('auth/login/', login_view, name='login'),
    path('auth/register/', register_view, name='register'),
    path('auth/logout/', logout_view, name='logout'),

    # Dashboard
    path('', dashboard_view, name='dashboard'),

    # Tenant management
    path('tenants/', tenant_list_view, name='tenant_list'),
    path('tenants/<uuid:pk>/', tenant_detail_view, name='tenant_detail'),
    path('tenants/<uuid:pk>/approve/', tenant_approve_view, name='tenant_approve'),
    path('tenants/<uuid:pk>/toggle-status/', tenant_toggle_status_view, name='tenant_toggle_status'),
]
