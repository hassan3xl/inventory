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

User = get_user_model()

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