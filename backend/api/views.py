import os

from django.db.models import Count, Exists, OuterRef, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from dotenv import load_dotenv
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.filters import IngredientsFilter, RecipeFilter
from api.pagination import CastomPagePagination
from api.permissins import IsAdminAuthorOrReadOnly, IsUserorAdmin
from api.serializers import (
    AvatarSerializer,
    CustomUserCreateSerializer,
    FavoriteSerializer,
    IngredientsSerializer,
    PasswordSerializer,
    RecipeSerializer,
    RecipeCreateUpdateSerializer,
    ShortRecipeSerializer,
    ShoppingCartSerializer,
    SubscriptionSerializer,
    TagsSerializer,
    UserSerializer,
)
from recipes.constants import INCORRECT_PASSWORD
from recipes.download_shopping_cart import shopping_list_file
from recipes.models import (
    Favorite,
    Ingredients,
    IngredientsRecipes,
    Recipes,
    ShoppingCart,
    Tags,
)
from users.models import Subscription, User


load_dotenv()


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингридиентов."""

    queryset = Ingredients.objects.all()
    serializer_class = IngredientsSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientsFilter


class RecipesViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов."""

    permission_classes = (IsAdminAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CastomPagePagination

    def get_queryset(self):
        """Добавление is_favorited и is_in_shopping_cart в get_queryset."""
        user = self.request.user
        queryset = Recipes.objects.all()

        if user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(Favorite.objects.filter(
                    user=user, recipes=OuterRef('pk'))),
                is_in_shopping_cart=Exists(ShoppingCart.objects.filter(
                    author=user, recipes=OuterRef('pk')))
            )
        return queryset

    def get_serializer_class(self):
        """Условие для выбора сериализатора."""
        if self.action in ('create', 'partial_update'):
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def add(self, model, user, pk, name):
        """Добавление рецепта."""
        recipes = get_object_or_404(Recipes, pk=pk)
        relation = model.objects.filter(user=user, recipes=recipes)
        if relation.exists():
            return Response(
                f'Нельзя повторно добавить рецепт в {name}',
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = FavoriteSerializer(
            data={'user': user.id, 'recipes': recipes.id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            ShortRecipeSerializer(recipes).data,
            status=status.HTTP_201_CREATED
        )

    def delete_relation(self, model, user, pk, name):
        """Удаление рецепта из списка пользователя."""
        deleted_count, _ = model.objects.filter(
            user=user, recipes__id=pk
        ).delete()
        if deleted_count == 0:
            return Response(
                f'Нельзя повторно удалить рецепт из {name}',
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='favorite',
        url_name='favorite',
    )
    def favorite(self, request, pk=None):
        """Добавление и удаление рецептов из избранного."""
        user = request.user
        if request.method == 'POST':
            name = 'избранное'
            return self.add(Favorite, user, pk, name)
        if request.method == 'DELETE':
            name = 'избранного'
            return self.delete_relation(Favorite, user, pk, name)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True,
            methods=('post', 'delete'),
            permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, **kwargs):
        """Добавить или удалить рецепт из списка покупок у пользоватeля."""
        user = self.request.user
        if request.method == 'POST':
            recipes = get_object_or_404(Recipes, id=self.kwargs.get('pk'))
            if ShoppingCart.objects.filter(
                author=user,
                recipes=recipes
            ).exists():
                return Response(
                    'Рецепт уже добавлен!',
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = ShoppingCartSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save(author=user, recipes=recipes)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED)
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            deleted_count, _ = ShoppingCart.objects.filter(
                author=user, recipes=self.kwargs.get('pk')).delete()
            if deleted_count == 0:
                return Response(
                    'Рецепт не найден в корзине.',
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                'Рецепт успешно удалён из списка покупок.',
                status=status.HTTP_204_NO_CONTENT
            )

    @action(detail=False,
            methods=('get',),
            permission_classes=[permissions.IsAuthenticated])
    def download_shopping_cart(self, request):
        """Скачать список покупок."""
        ingredients = IngredientsRecipes.objects.filter(
            recipes__in=ShoppingCart.objects.filter(
                author=self.request.user).values('recipes')
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        )

        file_name = 'shopping_list.txt'
        content_type = 'text/plain,charset=utf8'
        response = HttpResponse(
            shopping_list_file(ingredients), content_type=content_type
        )
        response['Content-Disposition'] = f'attachment; filename={file_name}'
        return response

    @action(
        detail=True,
        methods=('get',),
        url_path='get-link',
        url_name='get_link',
    )
    def get_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт."""
        recipes = get_object_or_404(Recipes, pk=pk)
        short_link = f'{os.getenv("DOMAIN")}/recipes/{recipes.id}'
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)


class TagsViewSet(viewsets.ModelViewSet):
    """Вьюсет для тегов."""

    queryset = Tags.objects.all()
    serializer_class = TagsSerializer
    permission_classes = (IsUserorAdmin,)
    http_method_names = ('get',)


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
