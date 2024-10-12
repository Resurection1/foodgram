from django.core.validators import MinValueValidator
from django.db import models

from api.constants import (
    INGREDIENTS_MAX_LENGTH_NAME,
    MAX_LENGTH_NAME,
    MAX_LENGTH_UNIT_NAME,
)
from users.models import (
    MyUser,
)


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

        constraints = (
            models.UniqueConstraint(
                fields=("name", "measurement_unit"),
                name="unique_ingredient",
            ),
        )

    def __str__(self):
        return self.name


class Recipes(models.Model):
    """Класс для модели рецепты."""

    author = models.ForeignKey(
        MyUser,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    name = models.CharField(
        max_length=MAX_LENGTH_NAME,
        verbose_name='Название',
    )
    image = models.ImageField(
        upload_to='recipes/',
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
        related_name='recipes',
        verbose_name='Ингридиенты'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время готовки'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации рецепта',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class IngredientsRecipes(models.Model):
    """Промежуточная модель для связи ингредиентов и рецептов."""

    recipes = models.ForeignKey(
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
        validators=(
            MinValueValidator(
                1, "Не может быть менее 1"
            ),
        ),
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        unique_together = ('recipes', 'ingredient')

    def __str__(self):
        return f"{self.ingredient.name} в {self.recipes.name} - {self.amount}"


class ShoppingCart(models.Model):
    """Класс для модели покупок."""

    author = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='shopping_list',
        verbose_name='Пользователь'
    )
    recipes = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='shopping_list',
        verbose_name='Рецепты'
    )

    class Meta:
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзины покупок'
        constraints = (
            models.UniqueConstraint(
                fields=('author', 'recipes'), name='shopping_list_recipe'
            ),
        )

    def __str__(self):
        return f'Корзина покупок {self.author.username}'


class Favorite(models.Model):
    user = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Пользователь',
    )
    recipes = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipes'), name='unique_favorite_recipe'
            ),
        )

    def __str__(self):
        return f'Рецепт {self.recipes} в избранном у пользователя {self.user}'
