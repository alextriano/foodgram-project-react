from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    RecipeViewSet,
    IngredientViewSet,
    TagViewSet,
    FollowViewSet,
    FavoriteViewSet,
    ShoppingCartViewSet,
    UserRetrieveViewSet,
)

app_name = 'api'

router = DefaultRouter()
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('download_shopping_cart/',
         RecipeViewSet.as_view({'get': 'download_shopping_cart'}),
         name='download_shopping_cart'),
    path('users/subscriptions/',
         FollowViewSet.as_view({'get': 'follows_list'}),
         name='follows_list'),
    path('users/<int:id>/subscribe/',
         FollowViewSet.as_view({'post': 'create', 'delete': 'destroy'}),
         name='follow'),
    path('recipes/<int:id>/favorite/',
         FavoriteViewSet.as_view({'post': 'create', 'delete': 'destroy'}),
         name='favorite'),
    path('recipes/<int:id>/shopping_cart/',
         ShoppingCartViewSet.as_view({'post': 'create', 'delete': 'destroy'}),
         name='shopping_cart'),
    path('auth/',
         include('djoser.urls.authtoken')),
    path('users/<int:pk>/',
         UserRetrieveViewSet.as_view(
             {'get': 'retrieve'})),
    path('',
         include('djoser.urls')),
    path('',
         include(router.urls)),
]
