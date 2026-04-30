# pyright: reportUnreachable=false


from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from rest_framework import status
from .serializers import CustomRegisterSerializer, LoginSerializer
from rest_framework.views import APIView
# from users.utils.send_otp import send_otp_email
# from users.models import OTPRequest

class OTPRequest():
    pass

def send_otp_email():
    pass 

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from dj_rest_auth.views import LoginView
from apps.tenants.models import TenantUser

User = get_user_model()

class TenantLoginView(LoginView):
    def post(self, request, *args, **kwargs):
        tenant = getattr(request, 'tenant', None)
        print(f"DEBUG: Login attempt on tenant: {tenant}")
        
        # Proceed with normal authentication
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            user = self.user
            print(f"DEBUG: User {user.email} authenticated. Checking tenant access...")
            
            # Verify user belongs to this tenant
            if not tenant:
                print("DEBUG: Login rejected: No tenant context.")
                return Response(
                    {"detail": "Business context not identified. Please use your subdomain."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            has_access = TenantUser.objects.filter(user=user, tenant=tenant).exists()
            if not has_access:
                print(f"DEBUG: Login rejected: User {user.email} does not belong to {tenant.subdomain}")
                return Response(
                    {"detail": f"Account '{user.email}' is not registered with '{tenant.name}'."},
                    status=status.HTTP_403_FORBIDDEN
                )
            print(f"DEBUG: Login successful for {user.email} on {tenant.subdomain}")
        
        return response

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    # callback_url must match EXACTLY what you put in Google Cloud Console
    callback_url = "http://localhost:3000" 
    client_class = OAuth2Client

    
class RequestOTPView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if user exists (for password reset flow)
        # For Registration, you might skip this check.
        if not User.objects.filter(email=email).exists():
             return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        send_otp_email(email)
        return Response({"message": "OTP sent successfully"})

class VerifyOTPView(APIView):
    def post(self, request):
        email = request.data.get('email')
        otp_code = request.data.get('otp')

        try:
            otp_record = OTPRequest.objects.get(email=email)
        except OTPRequest.DoesNotExist:
            return Response({"error": "Request new OTP"}, status=status.HTTP_400_BAD_REQUEST)

        if otp_record.otp_code == otp_code and otp_record.is_valid():
            # Mark as verified so it can be used for the next step (reset password)
            otp_record.is_verified = True
            otp_record.save()
            return Response({"message": "OTP Verified Successfully"})
        else:
            return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)
        

class ResetPasswordView(APIView):
    def post(self, request):
        email = request.data.get('email')
        new_password = request.data.get('new_password')
        
        # Security Check: Ensure OTP was verified recently
        try:
            otp_record = OTPRequest.objects.get(email=email)
            if not otp_record.is_verified:
                 return Response({"error": "Please verify OTP first"}, status=403)
        except OTPRequest.DoesNotExist:
             return Response({"error": "Invalid Request"}, status=403)

        # Reset Password
        user = User.objects.get(email=email)
        user.set_password(new_password)
        user.save()
        
        # Clean up used OTP
        otp_record.delete()
        
        return Response({"message": "Password reset successfully"})