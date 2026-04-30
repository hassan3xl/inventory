from django.urls import path
from .api_views import TenantDashboardAPIView, TenantListCreateAPIView

urlpatterns = [
    path('dashboard/', TenantDashboardAPIView.as_view(), name='api-tenant-dashboard'),
    path('list/', TenantListCreateAPIView.as_view(), name='api-tenant-list-create'),
]
