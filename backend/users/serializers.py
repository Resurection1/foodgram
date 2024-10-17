from django.contrib.auth import authenticate, password_validation
from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.constants import (
    INVALID_CREDENTIALS_ERROR,
    INACTIVE_ACCOUNT_ERROR,
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

    def validate(self, data):
        """Запрещает пользователям присваивать себе имя 'me'."""

        username = data.get('username')
        if username == NAME_ME:
            raise serializers.ValidationError(
                f'Использовать имя "{NAME_ME}" запрещено')

        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError(
                'Пользователь с таким username уже существует')

        return data


class CustomTokenCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для получения токена."""

    email = serializers.EmailField()
    password = serializers.CharField(
        required=False, style={'input_type': 'password'})

    class Meta():
        model = User
        fields = ['email', 'password']

    default_error_messages = {
        'invalid_credentials': INVALID_CREDENTIALS_ERROR,
        'inactive_account': INACTIVE_ACCOUNT_ERROR,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def validate(self, attrs):

        email = attrs.get('email')
        password = attrs.get('password')

        self.user = authenticate(request=self.context.get(
            'request'), email=email, password=password)

        if not self.user:
            self.user = User.objects.filter(email=email).first()
            if self.user and not self.user.check_password(password):
                self.fail('invalid_credentials')
            elif not self.user:
                self.fail('invalid_credentials')

        if not self.user.is_active:
            self.fail('inactive_account')

        attrs['user'] = self.user
        return attrs


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


class PasswordSerializer(serializers.Serializer):
    """Сериализатор для смены пароля."""

    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value
