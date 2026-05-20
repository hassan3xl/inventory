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
    subdomain = models.CharField(max_length=100, unique=True, null=True, blank=True, help_text="e.g., my-shop (optional, for future use)")
    business_type = models.CharField(max_length=50, choices=BusinessType.choices, default=BusinessType.GENERAL)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "tenants"

    def __str__(self):
        return self.name

class TenantUser(models.Model):
    """
    Links a platform User to a specific Tenant and assigns their in-store role.

    Store-level roles (lowest → highest authority):
        STAFF    — basic read/write on own tasks
        CASHIER  — can process sales / view pricing
        MANAGER  — can manage stock, staff tasks, and reports
        ADMIN    — full control of the store (invite staff, change settings)
        OWNER    — same as admin + can delete the store / transfer ownership
                   (typically the user whose User.role == TENANT)
    """

    class Role(models.TextChoices):
        OWNER   = 'owner',   'Owner'
        ADMIN   = 'admin',   'Administrator'
        MANAGER = 'manager', 'Manager'
        CASHIER = 'cashier', 'Cashier'
        STAFF   = 'staff',   'Staff'

    # Maps role → numeric rank so you can compare authority with >=
    ROLE_RANK = {
        Role.OWNER:   50,
        Role.ADMIN:   40,
        Role.MANAGER: 30,
        Role.CASHIER: 20,
        Role.STAFF:   10,
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='users')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='tenant_roles')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STAFF)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "tenant_users"
        unique_together = ('tenant', 'user')

    def __str__(self):
        return f"{self.user} — {self.tenant.name} ({self.get_role_display()})"

    def has_role_at_least(self, minimum_role: str) -> bool:
        """Check if this user's role is >= minimum_role in authority."""
        return self.ROLE_RANK.get(self.role, 0) >= self.ROLE_RANK.get(minimum_role, 0)

