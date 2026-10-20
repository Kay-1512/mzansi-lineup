from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    RegisterSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfileView(APIView):
    @extend_schema(responses=UserProfileSerializer)
    def get(self, request):
        return Response(UserProfileSerializer(request.user.profile).data)

    @extend_schema(request=UserProfileUpdateSerializer, responses=UserProfileSerializer)
    def patch(self, request):
        serializer = UserProfileUpdateSerializer(
            request.user.profile, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserProfileSerializer(request.user.profile).data)
