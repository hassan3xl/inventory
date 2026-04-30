    
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


from controllers.dashboard.views import BusinessProfileAPIView, StaffProfileAPIView, DashboardStatsAPIView

urlpatterns = [
    # Auth APIs
    path('auth/', include('controllers.auth.urls')),
    
    # Business & Staff APIs
    path('business/profile/', BusinessProfileAPIView.as_view(), name='api-business-profile'),
    path('staff/profile/', StaffProfileAPIView.as_view(), name='api-staff-profile'),
    path('dashboard/stats/', DashboardStatsAPIView.as_view(), name='api-dashboard-stats'),
    
    # User Profile APIs
    path('user/profile/', include('controllers.users.urls')),
]
