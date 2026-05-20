# Views have moved to api/controllers/tenants/views.py
# This shim preserves backwards-compatibility for any existing imports.
from api.controllers.tenants.views import (  # noqa: F401
    TenantRegisterAPIView,
    TenantListCreateAPIView,
    TenantDetailAPIView,
    TenantDashboardAPIView,
    TenantUserListAPIView,
)
