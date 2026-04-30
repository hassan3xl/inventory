from django.db import models
from django.utils import timezone
import uuid

class Tenant(models.Model):
    class BusinessType(models.TextChoices):
        GROCERY = 'grocery', 'Grocery Store'
        PHARMACY = 'pharmacy', 'Pharmacy & Medicine'
        ELECTRONICS = 'electronics', 'Electronics & Gadgets'
        CLOTHING = 'clothing', 'Clothing & Apparel'
        GENERAL = 'general', 'General Retail'
        OTHER = 'other', 'Other'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    subdomain = models.CharField(max_length=100, unique=True, help_text="e.g., my-shop")
    business_type = models.CharField(max_length=50, choices=BusinessType.choices, default=BusinessType.GENERAL)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "tenants"

    def __str__(self):
        return self.name

class TenantUser(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrator'
        MANAGER = 'manager', 'Manager'
        STAFF = 'staff', 'Staff'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='users')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='tenant_roles')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STAFF)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "tenant_users"
        unique_together = ('tenant', 'user')

    def __str__(self):
        return f"{self.user} - {self.tenant.name} ({self.get_role_display()})"
