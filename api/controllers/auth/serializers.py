from rest_framework import serializers
from django.contrib.auth import get_user_model
from dj_rest_auth.registration.serializers import RegisterSerializer
from django.db import transaction
from apps.users.models import Profile

User = get_user_model()


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
    """
    Returned on login and GET /api/auth/user/.
    Includes a `permissions` block that the frontend uses to show/hide
    sidebar items, action buttons, and protected routes — without making
    extra round-trips.

    permissions shape:
    {
        "platform_role": "tenant",
        "store_role": "manager",           // null if not in a store yet

        // UI flags — use these directly in the frontend
        "is_platform_admin": false,
        "is_owner":   false,
        "is_admin":   false,
        "is_manager": true,
        "is_cashier": true,   // true for manager and above
        "is_staff":   true,   // true for everyone in the store
    }
    """
    permissions = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'role', 'is_active', 'first_name', 'last_name', 'permissions')
        read_only_fields = ('email', 'role')

    def get_first_name(self, user):
        return user.profile.first_name if hasattr(user, 'profile') else ""

    def get_last_name(self, user):
        return user.profile.last_name if hasattr(user, 'profile') else ""


    def get_permissions(self, user):
        from apps.tenants.models import TenantUser

        # Resolve the tenant from context (set by TenantMiddleware / permission layer)
        request = self.context.get('request')
        tenant = getattr(request, 'tenant', None) if request else None

        # Find TenantUser for this tenant (or first one if no specific tenant)
        tenant_user = None
        if tenant:
            tenant_user = TenantUser.objects.filter(user=user, tenant=tenant).first()
        if not tenant_user:
            tenant_user = TenantUser.objects.filter(user=user).select_related('tenant').first()

        store_role = tenant_user.role if tenant_user else None
        rank = TenantUser.ROLE_RANK.get(store_role, 0) if store_role else 0

        return {
            # Raw roles — useful for debugging / storing in state
            "platform_role": user.role,
            "store_role": store_role,

            # Platform-level flag
            "is_platform_admin": user.is_platform_admin,

            # Store-level UI flags (cumulative — manager can do everything cashier can)
            "is_owner":   rank >= TenantUser.ROLE_RANK.get(TenantUser.Role.OWNER,   50),
            "is_admin":   rank >= TenantUser.ROLE_RANK.get(TenantUser.Role.ADMIN,   40),
            "is_manager": rank >= TenantUser.ROLE_RANK.get(TenantUser.Role.MANAGER, 30),
            "is_cashier": rank >= TenantUser.ROLE_RANK.get(TenantUser.Role.CASHIER, 20),
            "is_staff":   rank >= TenantUser.ROLE_RANK.get(TenantUser.Role.STAFF,   10),
        }
