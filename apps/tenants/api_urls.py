from django.urls import path
from .api_views import (
    TenantDashboardAPIView, 
    TenantListCreateAPIView,
    TenantRegisterAPIView,
    TenantUserListAPIView
)

urlpatterns = [
    path('register/', TenantRegisterAPIView.as_view(), name='api-tenant-register'),
    path('dashboard/', TenantDashboardAPIView.as_view(), name='api-tenant-dashboard'),
    path('list/', TenantListCreateAPIView.as_view(), name='api-tenant-list-create'),
    path('users/', TenantUserListAPIView.as_view(), name='api-tenant-users'),
