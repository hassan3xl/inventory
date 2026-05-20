from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
import uuid


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "platform_admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Platform-level user. The `role` field describes the user's relationship
    with the *platform*, not with any specific store.

        PLATFORM_ADMIN — internal ops / platform super-admin
        TENANT         — business owner (self-registered)
        STAFF          — store employee (provisioned by a tenant admin)
    """

    class RoleChoices(models.TextChoices):
        PLATFORM_ADMIN = "platform_admin", "Platform Admin"
        TENANT         = "tenant",         "Tenant (Business Owner)"
        STAFF          = "staff",          "Staff (Store Employee)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.TENANT,
    )
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.email

    # ── Convenience helpers used by serializers & permission classes ── #

    @property
    def is_platform_admin(self):
        return self.role == self.RoleChoices.PLATFORM_ADMIN

    @property
    def is_tenant_owner(self):
        return self.role == self.RoleChoices.TENANT

    @property
    def is_store_staff(self):
        return self.role == self.RoleChoices.STAFF
