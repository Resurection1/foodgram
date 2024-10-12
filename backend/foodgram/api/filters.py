from django_filters import ModelMultipleChoiceFilter
from django_filters.rest_framework import filters

from api.models import Recipes, Tags
from users.models import MyUser


class RecipeFilter(filters.FilterSet):
    """Класс с фильтрами для рецептов"""

    is_favorited = filters.BooleanFilter(method="favorited_method")
    is_in_shopping_cart = filters.BooleanFilter(
        method="in_shopping_cart_method")
    author = filters.ModelChoiceFilter(queryset=MyUser.objects.all())
    tags = ModelMultipleChoiceFilter(
        field_name="tags__slug",
        to_field_name="slug",
        queryset=Tags.objects.all(),
    )

    def favorited_method(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorite__user=self.request.user)
        return queryset

    def in_shopping_cart_method(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(shopping_list__author=self.request.user)
        return queryset

    class Meta:
        model = Recipes
        fields = ("author", "tags")
