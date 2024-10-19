from django.contrib.auth import password_validation
from djoser.serializers import UserCreateSerializer, TokenCreateSerializer
from rest_framework import serializers

from users.models import User


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
