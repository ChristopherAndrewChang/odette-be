from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import User
from .serializers import CreateAdminSerializer, UserSerializer, CustomTokenObtainPairSerializer
from .permissions import IsSuperuser, IsStaff
from rest_framework_simplejwt.views import TokenObtainPairView 
from apps.core.pagination import StandardPagination


class AdminAccountListCreateView(APIView):
    permission_classes = [IsSuperuser]

    def get(self, request):
        admins = User.objects.filter(
            role__in=[User.ROLE_ADMIN, User.ROLE_DJ, User.ROLE_CASHIER]
        ).order_by('username')

        paginator = StandardPagination()
        paginated = paginator.paginate_queryset(admins, request)
        serializer = UserSerializer(paginated, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        """Create a new admin account"""
        serializer = CreateAdminSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminAccountDetailView(APIView):
    permission_classes = [IsSuperuser]

    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk, role__in=[User.ROLE_ADMIN, User.ROLE_DJ, User.ROLE_CASHIER])
        except User.DoesNotExist:
            return None

    def patch(self, request, pk):
        """Deactivate or reactivate an admin account"""
        user = self.get_object(pk)
        if not user:
            return Response({'error': 'Admin not found'}, status=status.HTTP_404_NOT_FOUND)
        user.is_active = request.data.get('is_active', user.is_active)
        user.save()
        return Response(UserSerializer(user).data)

    def delete(self, request, pk):
        """Delete an admin account"""
        user = self.get_object(pk)
        if not user:
            return Response({'error': 'Admin not found'}, status=status.HTTP_404_NOT_FOUND)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class MeView(APIView):
    permission_classes = [IsStaff]

    def get(self, request):
        return Response({
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'role': request.user.role,
            'is_superuser_role': request.user.is_superuser_role,
            'is_admin_role': request.user.is_admin_role,
            'is_dj_role': request.user.is_dj_role,
            'is_cashier_role': request.user.is_cashier_role,
        })