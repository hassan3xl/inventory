from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import UserDetailSerializer


class AuthenticatedUserView(APIView):
    """
    GET /api/auth/user/
    Returns the authenticated user's profile plus their full permissions object.
    Call this after login to populate frontend state / local storage.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserDetailSerializer(request.user, context={'request': request})
        return Response(serializer.data)
