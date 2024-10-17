import os

from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from dotenv import load_dotenv
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from recipes.download_shopping_cart import shopping_list_file
from recipes.filters import RecipeFilter
from recipes.models import (
    Ingredients,
    IngredientsRecipes,
    Recipes,
    ShoppingCart,
    Tags,
    Favorite,
)
from recipes.pagination import CastomPagePagination
from recipes.permissins import IsAdminAuthorOrReadOnly, IsUserorAdmin
from recipes.serializers import (
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
    permission_classes = (IsUserorAdmin,)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        search_name = request.query_params.get('name', None)
        if search_name:
            queryset = queryset.filter(name__istartswith=search_name)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class RecipesViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов."""

    queryset = Recipes.objects.all()
    permission_classes = (IsAdminAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CastomPagePagination

    def get_serializer_class(self):
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
        model.objects.create(user=user, recipes=recipes)
        serializer = ShortRecipeSerializer(recipes)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_relation(self, model, user, pk, name):
        """Удаление рецепта из списка пользователя."""
        recipes = get_object_or_404(Recipes, pk=pk)
        relation = model.objects.filter(user=user, recipes=recipes)
        if not relation.exists():
            return Response(
                f'Нельзя повторно удалить рецепт из {name}',
                status=status.HTTP_400_BAD_REQUEST,
            )
        relation.delete()
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
        """Добавить или удалить  рецепт из списка покупок у пользоватля."""
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
            try:
                shopping_cart_item = ShoppingCart.objects.get(
                    author=user, recipes=recipes)
                shopping_cart_item.delete()
                return Response(
                    'Рецепт успешно удалён из списка покупок.',
                    status=status.HTTP_204_NO_CONTENT
                )
            except ShoppingCart.DoesNotExist:
                return Response(
                    'Рецепт не найден в корзине.',
                    status=status.HTTP_400_BAD_REQUEST
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

        return shopping_list_file(ingredients)

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
    http_method_names = ('get', 'post')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        self.check_permissions(request)

        allowed_fields = {'name', 'slug'}
        if request.data.keys() - allowed_fields != {'csrfmiddlewaretoken'}:
            return Response(
                'Method not allowed',
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)