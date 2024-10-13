from django.contrib import admin

from users.models import (
    MyUser,
    Subscription
)


@admin.register(MyUser)
class MyUserAdmin(admin.ModelAdmin):
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
    empty_value_display = 'значение отсутствует'
    list_filter = ('username',)
    search_fields = ('first_name', 'last_name', 'username', 'role')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Класс настройки раздела подписки."""

    list_display = (
        'id',
        'user',
        'author',

    )
    empty_value_display = 'значение отсутствует'
    list_filter = ('user',)
    search_fields = ('user',)
