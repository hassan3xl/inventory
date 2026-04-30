from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('tenants/', views.tenant_list_view, name='tenant_list'),
    path('tenants/<uuid:pk>/', views.tenant_detail_view, name='tenant_detail'),
]
