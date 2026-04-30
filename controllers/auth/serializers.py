from rest_framework import serializers
from django.contrib.auth import get_user_model

from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers

User = get_user_model()


from django.db import transaction
from apps.users.models import Profile

class CustomRegisterSerializer(RegisterSerializer):
    username = None 
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, email):
        email = email.lower()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return email

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data.pop("username", None)
        return data

    def save(self, request):
        with transaction.atomic():
            user = super().save(request)
            Profile.objects.create(
                user=user,
                first_name=self.validated_data.get('first_name', ''),
                last_name=self.validated_data.get('last_name', '')
            )
            return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'role', 'is_active')
        read_only_fields = ('email',)


