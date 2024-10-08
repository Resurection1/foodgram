from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.permissins import IsUserorAdmin
from api.pagination import CastomPagePagination
from api.models import Ingredients, Recipes, ShoppingCart, Tags
from api.serializers import (
    IngredientsSerializer,
    RecipesSerializer,
    TagsSerializer,
)


class IngredientsViewSet(viewsets.ModelViewSet):
    queryset = Ingredients.objects.all()
    serializer_class = IngredientsSerializer
    permission_classes = (IsUserorAdmin,)
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        search_name = request.query_params.get('name', None)

        if search_name:
            queryset = queryset.filter(name__istartswith=search_name)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class RecipesViewSet(viewsets.ModelViewSet):
    queryset = Recipes.objects.all()
    serializer_class = RecipesSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = CastomPagePagination
    # filter_backends = (DjangoFilterBackend,)

    # def perform_create(self, serializer):
    #     serializer.save(author=self.request.user)

    # @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    # def favorite(self, request, pk=None):
    #     recipe = self.get_object()
    #     recipe.favorited_by.add(request.user)
    #     return Response(status=status.HTTP_201_CREATED)

    # @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated])
    # def unfavorite(self, request, pk=None):
    #     recipe = self.get_object()
    #     recipe.favorited_by.remove(request.user)
    #     return Response(status=status.HTTP_204_NO_CONTENT)

    # @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    # def shopping_cart(self, request, pk=None):
    #     recipe = self.get_object()
    #     recipe.in_shopping_cart.add(request.user)
    #     return Response(status=status.HTTP_201_CREATED)

    # @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated])
    # def remove_from_cart(self, request, pk=None):
    #     recipe = self.get_object()
    #     recipe.in_shopping_cart.remove(request.user)
    #     return Response(status=status.HTTP_204_NO_CONTENT)


class TagsViewSet(viewsets.ModelViewSet):
    queryset = Tags.objects.all()
    serializer_class = TagsSerializer
    permission_classes = (IsUserorAdmin,)
    http_method_names = ['get', 'post']

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        self.check_permissions(request)

        allowed_fields = {'name', 'slug'}
        if request.data.keys() - allowed_fields != {'csrfmiddlewaretoken'}:
            return Response(
                {'detail': 'Method not allowed'},
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
