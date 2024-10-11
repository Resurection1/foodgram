
from rest_framework import exceptions, serializers
from django.core.validators import MinValueValidator
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField


from api.models import (
    Ingredients,
    Recipes,
    Tags,
    IngredientsRecipes,
    ShoppingCart,
    Favorite
)
from users.models import Subscription
from api.pagination import CastomPagePagination
from users.serializers import UserSerializer


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериалайзер модели корзина покупок."""

    name = serializers.ReadOnlyField(
        source='recipes.name',
        read_only=True)
    image = serializers.ImageField(
        source='recipes.image',
        read_only=True)
    cooking_time = serializers.IntegerField(
        source='recipes.cooking_time',
        read_only=True)
    id = serializers.PrimaryKeyRelatedField(
        source='recipes',
        read_only=True)

    class Meta:
        model = ShoppingCart
        fields = ('id', 'name', 'image', 'cooking_time')


class TagsSerializer(serializers.ModelSerializer):
    """Сериалазатор для модели тегов"""

    class Meta:
        model = Tags
        fields = ('id', 'name', 'slug',)


class IngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ингридиентов"""

    class Meta:
        model = Ingredients
        fields = ('id', 'name', 'measurement_unit',)


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipes
        fields = ("id", "name", "image", "cooking_time")


class SubscriptionSerializer(UserSerializer, CastomPagePagination):
    """Подписка."""

    email = serializers.ReadOnlyField(source="author.email")
    id = serializers.ReadOnlyField(source="author.id")
    username = serializers.ReadOnlyField(source="author.username")
    first_name = serializers.ReadOnlyField(source="author.first_name")
    last_name = serializers.ReadOnlyField(source="author.last_name")
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source="author.recipes.count")
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_subscribed",
            "recipes",
            "recipes_count",
            "avatar",
        )

    def get_recipes(self, obj):
        """Получение списка рецептов автора."""

        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = Recipes.objects.filter(author=obj.author)
        if limit and limit.isdigit():
            recipes = recipes[:int(limit)]
        return ShortRecipeSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        """Количество рецептов автора."""

        return Recipes.objects.filter(author=obj.id).count()

    def get_is_subscribed(self, obj):
        """Подписчики"""

        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user, author=obj.author
            ).exists()
        return False


class RecipeIngredientsSerializer(serializers.ModelSerializer):
    """Класс ингридиентов в рецептах."""

    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = IngredientsRecipes
        fields = ("id", "name", "measurement_unit", "amount")


class CreateUpdateRecipeIngredientsSerializer(serializers.ModelSerializer):
    """Класс создания и обновления ингридиентов в рецептах"""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredients.objects.all())
    amount = serializers.IntegerField(
        validators=(
            MinValueValidator(
                1, message="Количество ингредиентов не может быть меньше 1."
            ),
        )
    )

    class Meta:
        model = Ingredients
        fields = ("id", "amount")


class RecipeSerializer(serializers.ModelSerializer):
    """Класс рецептов"""

    author = UserSerializer(read_only=True)
    tags = TagsSerializer(many=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_ingredients(self, obj):
        ingredients = IngredientsRecipes.objects.filter(recipes=obj)
        serializer = RecipeIngredientsSerializer(ingredients, many=True)

        return serializer.data

    def get_is_favorited(self, obj):
        """Добавлен ли рецепт в избранное."""
        user_id = self.context.get('request').user.id
        return Favorite.objects.filter(user=user_id, recipes=obj.id).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if not user.is_anonymous:
            return ShoppingCart.objects.filter(recipes=obj).exists()
        return False

    class Meta:
        model = Recipes
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tags.objects.all(), many=True
    )
    author = UserSerializer(read_only=True)
    ingredients = CreateUpdateRecipeIngredientsSerializer(many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        validators=(
            MinValueValidator(
                1, message="Время приготовления не может быть меньше 1"
            ),
        )
    )

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                "Поле image обязательно для заполнения.")
        return value

    def validate_tags(self, value):
        if not value:
            raise exceptions.ValidationError("Добавьте хотя бы один тег!")
        elif len(value) != len(set(value)):
            raise serializers.ValidationError("Теги не должны повторяться.")
        return value

    def validate_ingredients(self, value):
        if not value:
            raise exceptions.ValidationError(
                "Добавьте хотя бы один ингредиент!"
            )

        ingredients = [item["id"] for item in value]
        for ingredient in ingredients:
            if ingredients.count(ingredient) > 1:
                raise exceptions.ValidationError(
                    "Рецепт не может включать два одинаковых ингредиента!"
                )

        return value

    def create(self, validated_data):
        author = self.context.get("request").user
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")

        recipes = Recipes.objects.create(author=author, **validated_data)
        recipes.tags.set(tags)

        for ingredient in ingredients:
            amount = ingredient.get("amount")
            ingredient = get_object_or_404(
                Ingredients, pk=ingredient.get("id").id
            )

            IngredientsRecipes.objects.create(
                recipes=recipes, ingredient=ingredient, amount=amount
            )

        return recipes

    def update(self, instance, validated_data):

        if "ingredients" not in validated_data:
            raise exceptions.ValidationError('Добавьте ингридиенты')
        elif "tags" not in validated_data:
            raise exceptions.ValidationError('Добавьте теги')
        tags = validated_data.pop("tags", None)
        if tags is not None:
            instance.tags.set(tags)

        ingredients = validated_data.pop("ingredients", None)
        if ingredients is not None:
            instance.ingredients.clear()

            for ingredient in ingredients:
                amount = ingredient.get("amount")
                ingredient = get_object_or_404(
                    Ingredients, pk=ingredient.get("id").id
                )

                IngredientsRecipes.objects.update_or_create(
                    recipes=instance,
                    ingredient=ingredient,
                    defaults={"amount": amount},
                )

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance, context={"request": self.context.get("request")}
        )

        return serializer.data

    class Meta:
        model = Recipes
        exclude = ("pub_date",)
