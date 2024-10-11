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
from users.models import MyUser, Subscription
from api.constants import INCORRECT_PASSWORD
from api.serializers import SubscriptionSerializer


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

    @action(
        detail=False,
        methods=("get",),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def subscriptions(self, request):
        """Список авторов, на которых подписан пользователь."""
        user = self.request.user
        queryset = user.follower.all()
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            pages, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=("post", "delete"))
    def subscribe(self, request, id=None):
        user = self.request.user
        author = get_object_or_404(MyUser, pk=id)

        if user == author:
            return Response(
                'Нельзя подписаться самому на себя)',
                status=status.HTTP_400_BAD_REQUEST,
            )

        elif not user.is_authenticated:
            return Response(
                'Необходимо зарегистрироваться',
                status=status.HTTP_401_UNAUTHORIZED
            )

        if self.request.method == "POST":
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {"errors": "Subscription already exists!"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            subscription = Subscription.objects.create(
                author=author, user=user)
            serializer = SubscriptionSerializer(
                subscription, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif self.request.method == "DELETE":
            if not Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {"errors": "You are not subscribed!"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            subscription = get_object_or_404(
                Subscription, user=user, author=author)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
