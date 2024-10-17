from django.contrib import admin

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
    empty_value_display = 'значение отсутствует'
    list_filter = ('name',)
    search_fields = ('name',)


@admin.register(Ingredients)
class IngredientAdmin(admin.ModelAdmin):
    """Класс настройки раздела ингридиенты."""

    list_display = (
        'id',
        'name',
        'measurement_unit',
    )
    empty_value_display = 'значение отсутствует'
    list_filter = ('name',)
    search_fields = ('name',)


class IngredientsInLine(admin.TabularInline):
    model = Recipes.ingredients.through
    extra = 1


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
    empty_value_display = 'значение отсутствует'
    list_filter = ('name', 'cooking_time', 'author')
    search_fields = ('name', 'text')
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
    empty_value_display = 'значение отсутствует'
    list_filter = ('recipes',)
    search_fields = ('recipes',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Класс настройки раздела избранные."""

    list_display = (
        'id',
        'user',
        'recipes',
    )
    empty_value_display = 'значение отсутствует'
    list_filter = ('user',)
    search_fields = ('user',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Класс настройки раздела корзина."""

    list_display = (
        'author',
        'recipes'
    )
    list_filter = ('author',)
    search_fields = ('author',)
