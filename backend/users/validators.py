from django.core.exceptions import ValidationError

from recipes.constants import NAME_ME


def username_validator(value):
    if value == NAME_ME:
        raise ValidationError(f'Использовать имя "{NAME_ME}" запрещено')
