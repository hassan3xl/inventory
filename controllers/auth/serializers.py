from rest_framework import serializers
from django.contrib.auth import get_user_model

from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers

User = get_user_model()


class CustomRegisterSerializer(RegisterSerializer):
    username = None 

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


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'role', 'is_active')
        read_only_fields = ('email',)


