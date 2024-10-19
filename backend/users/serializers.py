from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.constants import (
    NAME_ME,
)

from users.models import User, Subscription


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
        from recipes.serializers import ShortRecipeSerializer
        author_recipes = obj.recipes.all()
        serializer = ShortRecipeSerializer(author_recipes, many=True)
        return serializer.data
