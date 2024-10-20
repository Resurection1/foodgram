def shopping_list_file(ingredients):
    """Функция создания файла.txt"""
    lines = []
    for ingredient in ingredients:
        name = ingredient['ingredient__name']
        measurement_unit = ingredient['ingredient__measurement_unit']
        amount = ingredient['total_amount']
        lines.append(f'{name} ({measurement_unit}) - {amount}')
    content = '\n'.join(lines)
    return content
