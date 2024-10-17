from django.urls import include, path
from rest_framework import routers

from recipes.views import (
    IngredientsViewSet,
    RecipesViewSet,
    TagsViewSet,
)
from users.views import (
    UserViewSet
)

router = routers.DefaultRouter()
router.register(r'tags', TagsViewSet, basename='tags')
router.register(r'recipes', RecipesViewSet, basename='recipes')
router.register(
    r'ingredients', IngredientsViewSet, basename='ingredients')
router.register(r'users', UserViewSet, basename='users')


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
