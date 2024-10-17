from django.http import HttpResponse


def shopping_list_file(ingredients):
    """Функция создания файла.txt"""
    file_name = 'shopping_list.txt'
    lines = []
    for ing in ingredients:
        name = ing['ingredient__name']
        measurement_unit = ing['ingredient__measurement_unit']
        amount = ing['total_amount']
        lines.append(f'{name} ({measurement_unit}) - {amount}')
    content = '\n'.join(lines)
    content_type = 'text/plain,charset=utf8'
    response = HttpResponse(content, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename={file_name}'
    return response
