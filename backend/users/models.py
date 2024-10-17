from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from users.constants import (
    MAX_LENGTH_EMAIL,
    MAX_LENGTH_LASTNAME,
    MAX_LENGTH_ROLE,
    MAX_LENGTH_USERNAME,
    USERNAME_CHECK,
)
from users.validators import username_validator


class User(AbstractUser):
    """Класс для настройки модели юзера."""

    class Role(models.TextChoices):
        ADMIN = 'admin', _('Админ')
        USER = 'user', _('Пользователь')

    first_name = models.CharField(
        verbose_name='Имя',
        max_length=MAX_LENGTH_USERNAME,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=MAX_LENGTH_LASTNAME,
    )
    username = models.CharField(
        max_length=MAX_LENGTH_USERNAME,
        verbose_name='Имя пользователя',
        unique=True,
        db_index=True,
        validators=[RegexValidator(
            regex=USERNAME_CHECK,
            message='Имя пользователя содержит недопустимый символ'
        ),
            username_validator,
        ]
    )
    email = models.EmailField(
        max_length=MAX_LENGTH_EMAIL,
        verbose_name='email',
        unique=True
    )
    role = models.CharField(
        max_length=MAX_LENGTH_ROLE,
        choices=Role.choices,
        default=Role.USER)
    avatar = models.ImageField(
        upload_to='user/',
        null=True,
        default=None,
        verbose_name='Фотография',
    )

    @property
    def is_admin(self):
        return (self.role == self.Role.ADMIN
                or self.is_staff or self.is_superuser
                )

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Subscription(models.Model):
    """Модель подписки."""

    user = models.ForeignKey(
        User,
        related_name='follower',
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        related_name='subscribers',
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписчик'
        verbose_name_plural = 'Подписчики'
        unique_together = ('user', 'author')

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
