from rest_framework import serializers
from apps.users.models.profiles import Profile

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'user', 'first_name', 'last_name', 'bio', 'avatar', 'phone', 'email_notifications', 'created_at', 'updated_at']
