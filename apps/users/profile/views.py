from rest_framework import generics, permissions
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from apps.users.models.profiles import Profile
from apps.users.models.users import User
from apps.users.profile.serializers import ProfileSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.profile
