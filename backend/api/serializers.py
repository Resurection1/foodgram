from django.contrib.auth import password_validation
from django.core.validators import MinValueValidator
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, TokenCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import exceptions, serializers

from api.pagination import CastomPagePagination
from recipes.constants import (
    NAME_ME,
)
from recipes.models import (
    Favorite,
    Ingredients,
    IngredientsRecipes,
    Recipes,
    ShoppingCart,
    Tags,
)
from users.models import (
    User,
    Subscription,
)


class CustomUserCreateSerializer(UserCreateSerializer):
    """Кастомный сериализатор для создания объекта класса User."""

    class Meta(UserCreateSerializer.Meta):
        """Кастомный сериализатор для входа в аккаунт."""

        model = User
        fields = (
            'id', 'first_name',
            'last_name', 'username',
            'email', 'password',
        )


class CustomTokenCreateSerializer(TokenCreateSerializer):
    """Сериализатор для получения токена."""

    email = serializers.EmailField()
    password = serializers.CharField(
        required=False, style={'input_type': 'password'})

    class Meta():
        model = User
        fields = ['email', 'password']


class PasswordSerializer(serializers.Serializer):
    """Сериализатор для смены пароля."""

    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для аватара."""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ['avatar']

    def validate(self, data):
        """Проверка наличия аватара."""
        if data.get('avatar') is None:
            raise serializers.ValidationError('Данное поле обязательно.')
        return data


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели User."""

    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')

    def validate_username(self, username):
        if username == NAME_ME:
            raise serializers.ValidationError(
                f'Использовать имя "{NAME_ME}" запрещено'
            )
        return username

    def get_is_subscribed(self, obj):
        """Получение списка подписок."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user, author=obj
            ).exists()
        return False

    def get_recipes(self, obj):
        """Получение списка рецептов автора."""
        from api.serializers import ShortRecipeSerializer
        author_recipes = obj.recipes.all()
        serializer = ShortRecipeSerializer(author_recipes, many=True)
        return serializer.data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сереализатор для рцепептов в избранные."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipes',)


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
    """Класс для рецептов, но укороченный"""

    class Meta:
        model = Recipes
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(UserSerializer, CastomPagePagination):
    """Подписка."""

    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def to_representation(self, instance):
        """Добавление аннотированных полей к сериализованному представлению."""
        representation = super().to_representation(instance)
        representation['recipes_count'] = getattr(
            instance, 'recipes_count', 0
        )

        return representation

    def get_recipes(self, obj):
        """Получение списка рецептов автора."""
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = Recipes.objects.filter(author=obj.author)
        if limit and limit.isdigit():
            recipes = recipes[:int(limit)]
        return ShortRecipeSerializer(recipes, many=True).data

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

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientsRecipes
        fields = ('id', 'name', 'measurement_unit', 'amount')


class CreateUpdateRecipeIngredientsSerializer(serializers.ModelSerializer):
    """Класс создания и обновления ингридиентов в рецептах"""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredients.objects.all())
    amount = serializers.IntegerField(
        validators=(
            MinValueValidator(
                1, message='Количество ингредиентов не может быть меньше 1.'
            ),
        )
    )

    class Meta:
        model = Ingredients
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Класс рецептов"""

    author = UserSerializer(read_only=True)
    tags = TagsSerializer(many=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

    class Meta:
        model = Recipes
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')

    def get_ingredients(self, obj):
        """Получение ингридиентов."""
        ingredients = IngredientsRecipes.objects.filter(recipes=obj)
        serializer = RecipeIngredientsSerializer(ingredients, many=True)

        return serializer.data

    def to_representation(self, instance):
        """Добавление аннотированных полей к сериализованному представлению."""
        representation = super().to_representation(instance)
        representation['is_favorited'] = getattr(
            instance, 'is_favorited', False
        )
        representation['is_in_shopping_cart'] = getattr(
            instance, 'is_in_shopping_cart', False
        )
        return representation


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Класс обновления и создания рецептов."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tags.objects.all(), many=True
    )
    author = UserSerializer(read_only=True)
    ingredients = CreateUpdateRecipeIngredientsSerializer(many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        validators=(
            MinValueValidator(
                1, message='Время приготовления не может быть меньше 1'
            ),
        )
    )

    class Meta:
        model = Recipes
        fields = (
            'id', 'tags', 'author',
            'ingredients', 'name', 'image',
            'text', 'cooking_time'
        )

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                'Поле image обязательно для заполнения.')
        return value

    def validate_tags(self, value):
        if not value:
            raise exceptions.ValidationError('Добавьте хотя бы один тег!')
        elif len(value) != len(set(value)):
            raise serializers.ValidationError('Теги не должны повторяться.')
        return value

    def validate_ingredients(self, value):
        if not value:
            raise exceptions.ValidationError(
                'Добавьте хотя бы один ингредиент!'
            )

        ingredients = [item['id'] for item in value]
        for ingredient in ingredients:
            if ingredients.count(ingredient) > 1:
                raise exceptions.ValidationError(
                    'Рецепт не может включать два одинаковых ингредиента!'
                )

        return value

    def create(self, validated_data):
        """Создание."""
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        recipes = Recipes.objects.create(author=author, **validated_data)
        self._set_tags_and_ingredients(recipes, tags, ingredients)

        return recipes

    def update(self, instance, validated_data):
        """Обновление."""
        if 'ingredients' not in validated_data:
            raise exceptions.ValidationError('Добавьте ингридиенты')
        elif 'tags' not in validated_data:
            raise exceptions.ValidationError('Добавьте теги')

        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)

        if tags is not None:
            instance.tags.set(tags)

        if ingredients is not None:
            self._set_tags_and_ingredients(instance, tags, ingredients)

        return super().update(instance, validated_data)

    def _set_tags_and_ingredients(self, recipe_instance, tags, ingredients):
        """Устанавливает теги и ингредиенты для рецепта."""
        recipe_instance.tags.set(tags)
        recipe_instance.ingredients.clear()

        for ingredient in ingredients:
            amount = ingredient.get('amount')
            ingredient_instance = get_object_or_404(
                Ingredients, pk=ingredient.get('id').id
            )

            IngredientsRecipes.objects.update_or_create(
                recipes=recipe_instance,
                ingredient=ingredient_instance,
                defaults={'amount': amount},
            )

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance, context={'request': self.context.get('request')}
        )

        return serializer.data
