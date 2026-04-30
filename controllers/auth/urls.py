from django.urls import path
from .views import GoogleLogin, RequestOTPView, VerifyOTPView, ResetPasswordView, TenantLoginView
from .user_view import AuthenticatedUserView
from django.urls import path, include
from rest_framework_simplejwt.views import TokenVerifyView, TokenRefreshView

urlpatterns = [
    # 1. Standard Auth (Overriding Login with Tenant-Aware Login)
    path('login/', TenantLoginView.as_view(), name='rest_login'),
    path('', include('dj_rest_auth.urls')),

    # 2. Registration (Uses your CustomRegisterSerializer)
    path('register/', include('dj_rest_auth.registration.urls')),

    # 3. Google Auth
    path('google/', GoogleLogin.as_view(), name='google_login'),

    # 4. Token Management (The missing link!)
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # 5. Your Custom OTP Password Reset (Keep your existing views here)
    path('otp/request/', RequestOTPView.as_view(), name='otp_request'),
    path('otp/verify/', VerifyOTPView.as_view(), name='otp_verify'),
    path('password-reset/', ResetPasswordView.as_view(), name='password_reset'),

    # 6. Authenticated user endpoint
    path('user/', AuthenticatedUserView.as_view(), name='authenticated-user'),
]