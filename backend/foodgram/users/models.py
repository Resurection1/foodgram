from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from api.constants import (
    MAX_LENGTH_EMAIL,
    MAX_LENGTH_LASTNAME,
    MAX_LENGTH_ROLE,
    MAX_LENGTH_USERNAME,
    USERNAME_CHECK,
)


class MyUser(AbstractUser):
    """Класс для настройки модели юзера."""

    ADMIN = "admin"
    USER = "user"
    CHOICES = [
        (USER, 'user'),
        (ADMIN, 'admin')
    ]
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
        )]
    )
    email = models.EmailField(
        max_length=MAX_LENGTH_EMAIL,
        verbose_name='email',
        unique=True
    )
    role = models.CharField(
        max_length=MAX_LENGTH_ROLE,
        choices=CHOICES,
        default='user')
    avatar = models.ImageField(
        upload_to='user/',
        null=True,
        default=None,
        verbose_name='Фотография',
    )
    is_subscribed = models.ManyToManyField(
        'Subscription',
        related_name='subscribers',
        blank=True,
    )

    @property
    def is_admin(self):
        return self.role == self.ADMIN or self.is_staff


class Subscription(models.Model):
    """Модель подписки, которая определяет отношения между пользователями."""

    user = models.ForeignKey(
        MyUser,
        related_name='subscriptions',
        on_delete=models.CASCADE
    )
    subscribed_to = models.ForeignKey(
        MyUser,
        related_name='subscribers',
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('user', 'subscribed_to')