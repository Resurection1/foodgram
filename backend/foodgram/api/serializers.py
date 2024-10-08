
from rest_framework import serializers

from api.models import Ingredients, Recipes, Tags, IngredientsRecipes


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


class RecipesSerializer(serializers.ModelSerializer):
    """Сериализатор для модели рецептов"""

    author = serializers.ReadOnlyField(source='author.username')
    ingredients = IngredientsSerializer(
        many=True, source='recipeingredient_set')
    tags = TagsSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipes
        fields = (
            'id', 'tags', 'author',
            'ingredients', 'name',
            'image', 'text',
            'cooking_time', 'is_favorited', 'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and obj.favorited_by.filter(
            id=user.id
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and obj.in_shopping_cart.filter(
            id=user.id
        ).exists()

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipes.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        for ingredient_data in ingredients_data:
            IngredientsRecipes.objects.create(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
        return recipe
