from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.pagination import CastomPagePagination
from api.permissins import (
    IsUserorAdmin,
)
from api.serializers import (
    AvatarSerializer,
    CustomUserCreateSerializer,
    PasswordSerializer,
    UserSerializer,
)
from recipes.constants import INCORRECT_PASSWORD
from recipes.serializers import SubscriptionSerializer
from users.models import User, Subscription


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели User."""

    queryset = User.objects.order_by('id')
    permission_classes = (IsUserorAdmin, )
    pagination_class = CastomPagePagination
    filter_backends = (filters.SearchFilter, )
    filterset_fields = ('id',)
    search_fields = ('id', )
    lookup_field = 'id'
    http_method_names = (
        'get', 'patch', 'post', 'delete', 'put',
    )

    def get_serializer_class(self):
        """Условие для выбора сериализатора."""
        if self.action == 'create':
            return CustomUserCreateSerializer
        return UserSerializer

    @action(
        methods=('post',),
        detail=False,
        url_path='set_password',
        permission_classes=(permissions.IsAuthenticated, )
    )
    def set_password(self, request):
        """Смена пароля."""
        user = request.user
        serializer = PasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        if not user.check_password(
            serializer.validated_data['current_password']
        ):
            return Response(
                {'current_password': INCORRECT_PASSWORD},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=('get', 'patch'),
        detail=False,
        url_path='me',
        permission_classes=(permissions.IsAuthenticated, )
    )
    def get_patch_me(self, request):
        """Получение или изменения страницы me."""
        if request.method == 'GET':
            serializer = UserSerializer(request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(role=request.user.role)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=('put', 'delete'),
        detail=False,
        url_path='me/avatar',
        permission_classes=(permissions.IsAuthenticated, )
    )
    def put_avatar(self, request):
        """Изменение аватара."""
        user = get_object_or_404(User, username=request.user.username)
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

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def subscriptions(self, request):
        """Список авторов, на которых подписан пользователь."""
        user = self.request.user
        queryset = user.follower.annotate(
            recipes_count=Count('author__recipes')
        )
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def subscribe(self, request, id=None):
        """Подписка."""
        user = self.request.user
        if self.request.method == 'POST':
            author = get_object_or_404(User, pk=id)
            if user == author:
                return Response(
                    'Нельзя подписаться самому на себя)',
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    'Подписка уже существует.',
                    status=status.HTTP_400_BAD_REQUEST,
                )

            subscription = Subscription.objects.create(
                author=author, user=user)
            serializer = SubscriptionSerializer(
                subscription, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif self.request.method == 'DELETE':
            deleted_count, _ = Subscription.objects.filter(
                user=user, author=id
            ).delete()
            if deleted_count == 0:
                return Response(
                    'Вы не подписаны',
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(status=status.HTTP_204_NO_CONTENT)
