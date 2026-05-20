from rest_framework import serializers
from .models import Tenant, TenantUser

class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['id', 'name', 'business_type', 'is_active', 'created_at']

class TenantDashboardSerializer(serializers.Serializer):
    total_products = serializers.IntegerField(default=0)
    total_staff = serializers.IntegerField(default=0)
    business_name = serializers.CharField()
    business_type = serializers.CharField()
