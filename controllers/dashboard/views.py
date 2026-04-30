from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from apps.tenants.models import Tenant, TenantUser
from apps.tenants.permissions.tenant_roles import HasTenantAccess, IsTenantAdmin, IsTenantManager
from apps.tenants.serializers import TenantSerializer, TenantDashboardSerializer

class BusinessProfileAPIView(APIView):
    permission_classes = [IsAuthenticated, HasTenantAccess]

    def get(self, request):
        tenant = request.tenant
        return Response({
            "id": tenant.id,
            "name": tenant.name,
            "subdomain": tenant.subdomain,
            "category": tenant.get_business_type_display(),
            "is_active": tenant.is_active,
            "created_at": tenant.created_at
        })

class StaffProfileAPIView(APIView):
    permission_classes = [IsAuthenticated, HasTenantAccess]

    def get(self, request):
        tenant = request.tenant
        tenant_user = TenantUser.objects.get(user=request.user, tenant=tenant)

        return Response({
            "email": request.user.email,
            "role": tenant_user.role,
            "role_display": tenant_user.get_role_display(),
            "joined_at": tenant_user.created_at
        })

class DashboardStatsAPIView(APIView):
    permission_classes = [IsAuthenticated, HasTenantAccess]

    def get(self, request):
        tenant = request.tenant
        
        return Response({
            "total_products": 0,
            "total_staff": tenant.users.count(),
            "recent_activity": []
        })

class StaffListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsTenantManager]
    
    def get(self, request):
        tenant = request.tenant
        staff = TenantUser.objects.filter(tenant=tenant).select_related('user', 'user__profile')
        
        data = []
        for s in staff:
            profile = getattr(s.user, 'profile', None)
            if profile and (profile.first_name or profile.last_name):
                full_name = f"{profile.first_name} {profile.last_name}".strip()
            else:
                full_name = s.user.email.split('@')[0] # Fallback to email prefix
            
            data.append({
                "id": s.user.id,
                "email": s.user.email,
                "full_name": full_name,
                "role": s.role,
                "role_display": s.get_role_display(),
                "date_joined": s.created_at
            })
        
        return Response(data)

class StaffAddAPIView(APIView):
    permission_classes = [IsAuthenticated, IsTenantAdmin]

    def post(self, request):
        tenant = request.tenant
        email = request.data.get('email')
        role = request.data.get('role', 'STAFF')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')

        if not email:
            return Response({"error": "Email is required"}, status=400)

        from django.contrib.auth import get_user_model
        from django.db import transaction
        from apps.users.models import Profile
        User = get_user_model()

        try:
            with transaction.atomic():
                # 1. Create or get User (Only email)
                user, created = User.objects.get_or_create(email=email)

                if created:
                    import string
                    import random
                    password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
                    user.set_password(password)
                    user.save()
                    # In a real app, send email here
                    print(f"DEBUG: Provisioned staff {email} with password: {password}")

                # 2. Create or Update Profile
                Profile.objects.update_or_create(
                    user=user,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name
                    }
                )

                # 3. Check if already a staff of this tenant
                if TenantUser.objects.filter(user=user, tenant=tenant).exists():
                    return Response({"detail": "User is already a staff member of this business"}, status=400)

                # 4. Link to Tenant
                TenantUser.objects.create(user=user, tenant=tenant, role=role)

                return Response({
                    "message": "Staff added successfully",
                    "email": email,
                    "role": role
                }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": f"Failed to add staff: {str(e)}"}, status=500)

