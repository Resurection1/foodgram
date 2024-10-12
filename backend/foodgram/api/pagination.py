from rest_framework.pagination import PageNumberPagination


class CastomPagePagination(PageNumberPagination):
    """Класс для кастомного пагинатора"""

    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 100
