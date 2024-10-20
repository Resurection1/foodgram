import os

from django.db.models import Exists, OuterRef, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from dotenv import load_dotenv
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from recipes.download_shopping_cart import shopping_list_file
from recipes.filters import IngredientsFilter, RecipeFilter
from recipes.models import (
    Favorite,
    Ingredients,
    IngredientsRecipes,
    Recipes,
    ShoppingCart,
    Tags,
)
from recipes.pagination import CastomPagePagination
from recipes.permissins import IsAdminAuthorOrReadOnly, IsUserorAdmin
from recipes.serializers import (
    FavoriteSerializer,
    IngredientsSerializer,
    TagsSerializer,
    RecipeSerializer,
    RecipeCreateUpdateSerializer,
    ShortRecipeSerializer,
    ShoppingCartSerializer,
)


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
        recipe_serializer = ShortRecipeSerializer(recipes)
        return Response(recipe_serializer.data, status=status.HTTP_201_CREATED)

    def delete_relation(self, model, user, pk, name):
        """Удаление рецепта из списка пользователя."""
        recipes = get_object_or_404(Recipes, pk=pk)
        deleted_count, _ = model.objects.filter(
            user=user, recipes=recipes
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
        recipes = get_object_or_404(Recipes, id=self.kwargs.get('pk'))
        user = self.request.user
        if request.method == 'POST':
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
                author=user, recipes=recipes).delete()
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
