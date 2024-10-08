from django.shortcuts import get_object_or_404
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.pagination import CastomPagePagination
from api.permissins import (

    IsUserorAdmin,
)
from users.serializers import (
    AvatarSerializer,
    UserSerializer,
    CustomUserCreateSerializer,
    PasswordSerializer
)
from users.models import MyUser
from api.constants import INCORRECT_PASSWORD


class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = MyUser.objects.all()
    serializer_class = UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = MyUser.objects.all().order_by('id')
    permission_classes = (IsUserorAdmin, )
    pagination_class = CastomPagePagination
    filter_backends = (filters.SearchFilter, )
    filterset_fields = ('id')
    search_fields = ('id', )
    lookup_field = 'id'
    http_method_names = [
        'get', 'patch', 'post', 'delete', 'put',
    ]

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        return UserSerializer

    @action(
        methods=['post'],
        detail=False,
        url_path='set_password',
        permission_classes=(permissions.IsAuthenticated, )
    )
    def set_password(self, request):
        user = request.user
        serializer = PasswordSerializer(data=request.data)

        if serializer.is_valid():
            if not user.check_password(
                serializer.validated_data['current_password']
            ):
                return Response(
                    {"current_password": INCORRECT_PASSWORD},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['get', 'patch'],
        detail=False,
        url_path='me',
        permission_classes=(permissions.IsAuthenticated, )
    )
    def get_patch_me(self, request):
        user = get_object_or_404(MyUser, username=self.request.user)
        if request.method == 'GET':
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = UserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(role=user.role)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['put', 'delete'],
        detail=False,
        url_path='me/avatar',
        permission_classes=(permissions.IsAuthenticated, )
    )
    def put_avatar(self, request):
        user = get_object_or_404(MyUser, username=request.user.username)

        if request.method == 'PUT':
            if 'avatar' not in request.data:
                return Response(
                    {'error': 'The avatar field is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = AvatarSerializer(user, data=request.data, partial=True)

        if request.method == 'PUT':
            serializer = AvatarSerializer(
                user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {'avatar': user.avatar.url},
                    status=status.HTTP_200_OK
                )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        elif request.method == 'DELETE':
            user.avatar.delete()
            user.avatar = None
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
