from django.urls import path
from .views import (
    TenantRegisterAPIView,
    TenantListCreateAPIView,
    TenantDetailAPIView,
    TenantDashboardAPIView,
    TenantUserListAPIView,
)

urlpatterns = [
    path('register/',  TenantRegisterAPIView.as_view(),   name='api-tenant-register'),
    path('',           TenantListCreateAPIView.as_view(), name='api-tenant-list-create'),
    path('me/',        TenantDetailAPIView.as_view(),     name='api-tenant-detail'),
    path('dashboard/', TenantDashboardAPIView.as_view(),  name='api-tenant-dashboard'),
    path('users/',     TenantUserListAPIView.as_view(),   name='api-tenant-users'),
]
