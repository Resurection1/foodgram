from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from users.models import (
    User,
    Subscription
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Класс настройки раздела пользователи."""

    list_display = (
        'id',
        'first_name',
        'last_name',
        'username',
        'email',
        'role',
        'avatar',
    )
    list_display_links = ('first_name',)
    empty_value_display = 'значение отсутствует'
    search_fields = ('first_name', 'last_name', 'username', 'role', 'email',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Класс настройки раздела подписки."""

    list_display = (
        'id',
        'user',
        'author',

    )
    list_display_links = ('id', 'user',)
    empty_value_display = 'значение отсутствует'
    search_fields = ('user',)
