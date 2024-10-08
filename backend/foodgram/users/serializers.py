
import base64

from django.core.files.base import ContentFile
from django.contrib.auth import authenticate, password_validation
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers

from api.constants import (
    INVALID_CREDENTIALS_ERROR,
    INACTIVE_ACCOUNT_ERROR,
    NAME_ME,
)
from users.models import MyUser, Subscription
from api.models import Recipes
from api.serializers import RecipesSerializer


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = MyUser
        fields = ['avatar']


class CustomUserCreateSerializer(UserCreateSerializer):
    """Кастомный сериализатор для создания объекта класса MyUser."""

    class Meta(UserCreateSerializer.Meta):
        """Кастомный сериализатор для входа в аккаунт."""
        model = MyUser
        fields = (
            'id', 'first_name',
            'last_name', 'username',
            'email', 'password',
        )

    def validate(self, data):
        """Запрещает пользователям присваивать себе имя 'me'."""

        email = data.get('email')
        username = data.get('username')
        if MyUser.objects.all().filter(email=email, username=username):
            return data

        if username == NAME_ME:
            raise serializers.ValidationError(
                f'Использовать имя "{NAME_ME}" запрещено')

        if MyUser.objects.filter(username=username).exists():
            raise serializers.ValidationError(
                'Пользователь с таким username уже существует')

        if MyUser.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                'Пользователь с таким email уже существует')
        return data


class CustomTokenCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        required=False, style={"input_type": "password"})

    class Meta():
        model = MyUser
        fields = ['email', 'password']

    default_error_messages = {
        "invalid_credentials": INVALID_CREDENTIALS_ERROR,
        "inactive_account": INACTIVE_ACCOUNT_ERROR,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def validate(self, attrs):

        email = attrs.get("email")
        password = attrs.get("password")

        self.user = authenticate(request=self.context.get(
            "request"), email=email, password=password)

        if not self.user:
            self.user = MyUser.objects.filter(email=email).first()
            if self.user and not self.user.check_password(password):
                self.fail("invalid_credentials")
            elif not self.user:
                self.fail("invalid_credentials")

        if not self.user.is_active:
            self.fail("inactive_account")

        attrs['user'] = self.user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели MyUser."""

    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = MyUser
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')

    def validate_username(self, username):
        if username == NAME_ME:
            raise serializers.ValidationError(
                f'Использовать имя "{NAME_ME}" запрещено'
            )
        return username

    def update(self, instance, validated_data):
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.save()
        return instance

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes = Recipes.objects.filter(author=obj)
        if limit:
            recipes = recipes[:int(limit)]
        return RecipesSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return Recipes.objects.filter(author=obj).count()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user, subscribed_to=obj
            ).exists()
        return False


class PasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value
