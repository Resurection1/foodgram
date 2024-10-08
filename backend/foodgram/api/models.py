from django.contrib.auth import get_user_model
from django.db import models

from api.constants import (
    MAX_LENGTH_NAME,
    MAX_LENGTH_UNIT_NAME,
    INGREDIENTS_MAX_LENGTH_NAME,
)

Author = get_user_model()


class Tags(models.Model):
    """Класс для модели теги."""

    name = models.CharField(
        verbose_name='Имя',
        max_length=MAX_LENGTH_NAME,
    )
    slug = models.SlugField(
        unique=True,
        max_length=MAX_LENGTH_NAME,
        verbose_name='Идентификатор'
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name


class Ingredients(models.Model):
    """Класс для модели ингридиенты."""

    KG = 'кг'
    GRAM = 'гр'
    CHOICES = [
        ('кг', KG),
        ('гр', GRAM),
    ]
    name = models.CharField(
        max_length=INGREDIENTS_MAX_LENGTH_NAME,
        verbose_name='Название',
    )
    measurement_unit = models.CharField(
        max_length=MAX_LENGTH_UNIT_NAME,
        choices=CHOICES,
        verbose_name='Вес',
    )

    class Meta:
        verbose_name = "Ингридиент"
        verbose_name_plural = "Ингридиенты"

    def __str__(self):
        return self.name


class Recipes(models.Model):
    """Класс для модели рецепты."""

    author = models.ForeignKey(
        Author, related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    name = models.CharField(
        max_length=MAX_LENGTH_NAME,
        verbose_name='Название',
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        null=True,
        default=None,
        verbose_name='Фотография',
    )
    text = models.TextField(
        verbose_name='Текст'
    )
    tags = models.ManyToManyField(
        Tags,
        related_name='recipes',
    )
    ingredients = models.ManyToManyField(
        Ingredients,
        through='IngredientsRecipes',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время готовки'
    )
    is_favorited = models.BooleanField(
        default=False,
    )
    is_in_shopping_cart = models.BooleanField(
        default=False,
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class IngredientsRecipes(models.Model):
    """Промежуточная модель для связи ингредиентов и рецептов."""

    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredients,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"
        unique_together = ('recipe', 'ingredient')

    def __str__(self):
        return f"{self.ingredient.title} в {self.recipe.name} - {self.amount}"


class ShoppingCart(models.Model):
    """Класс для модели покупок."""

    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )
    recipes = models.ManyToManyField(
        Recipes,
        related_name='in_shopping_cart',
        verbose_name='Рецепты'
    )

    class Meta:
        verbose_name = "Корзина покупок"
        verbose_name_plural = "Корзины покупок"

    def __str__(self):
        return f"Корзина покупок {self.user.username}"

    def get_ingredient_summary(self):
        """
        Возвращает суммированный список ингредиентов для рецептов в корзине
        """
        ingredients_summary = {}
        for recipe in self.recipes.all():
            for ingredient in recipe.ingredients.all():
                amount = IngredientsRecipes.objects.get(
                    recipe=recipe, ingredient=ingredient).amount
                if ingredient.title in ingredients_summary:
                    ingredients_summary[ingredient.title] += amount
                else:
                    ingredients_summary[ingredient.title] = amount
        return ingredients_summary
