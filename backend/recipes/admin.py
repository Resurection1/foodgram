from django.contrib import admin
from admin_auto_filters.filters import AutocompleteFilter

from recipes.models import (
    Favorite,
    Ingredients,
    IngredientsRecipes,
    Recipes,
    ShoppingCart,
    Tags,
)


@admin.register(Tags)
class TagAdmin(admin.ModelAdmin):
    """Класс настройки раздела тегов."""

    list_display = (
        'id',
        'name',
        'slug',
    )
    list_display_links = ('id', 'name',)
    empty_value_display = 'значение отсутствует'
    search_fields = ('name',)


@admin.register(Ingredients)
class IngredientAdmin(admin.ModelAdmin):
    """Класс настройки раздела ингридиенты."""

    list_display = (
        'id',
        'name',
        'measurement_unit',
    )
    list_display_links = ('id', 'name',)
    empty_value_display = 'значение отсутствует'
    search_fields = ('name',)


class IngredientsInLine(admin.TabularInline):
    """Класс для создания ингредиентов в рецептах."""

    model = Recipes.ingredients.through
    extra = 1


class RecipesAuthorFilters(AutocompleteFilter):
    """Класс фильтров для рецептов в админ панели."""

    title = 'Author'
    field_name = 'author'


@admin.register(Recipes)
class RecipeAdmin(admin.ModelAdmin):
    """Класс настройки раздела рецепты."""

    list_display = (
        'id',
        'name',
        'text',
        'cooking_time',
        'author',
        'image',
        'pub_date'
    )
    list_display_links = ('id', 'name',)
    empty_value_display = 'значение отсутствует'
    list_filter = (RecipesAuthorFilters, 'cooking_time',)
    search_fields = ('name',)
    inlines = (IngredientsInLine, )


@admin.register(IngredientsRecipes)
class IngredientRecipeAdmin(admin.ModelAdmin):
    """Класс настройки раздела ингридиенты в рецепте."""

    list_display = (
        'id',
        'recipes',
        'ingredient',
        'amount',
    )
    list_display_links = ('id', 'recipes',)
    empty_value_display = 'значение отсутствует'
    list_filter = ('recipes',)
    search_fields = ('recipes__name',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Класс настройки раздела избранные."""

    list_display = (
        'id',
        'user',
        'recipes',
    )
    list_display_links = ('id', 'user',)
    empty_value_display = 'значение отсутствует'
    search_fields = ('user__username',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Класс настройки раздела корзина."""

    list_display = (
        'id',
        'author',
        'recipes'
    )
    search_fields = ('author__username',)
    list_filter = [RecipesAuthorFilters]
