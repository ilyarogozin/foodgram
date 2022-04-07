from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (IngredientViewSet, RecipeViewSet, TagViewSet,
                    add_recipe_to_favorites, add_recipe_to_shopping_cart,
                    download_shopping_cart)

app_name = 'recipes'

router_v1 = DefaultRouter()
router_v1.register(r'tags', TagViewSet, basename='tags')
router_v1.register(r'recipes', RecipeViewSet, basename='recipes')
router_v1.register(r'ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('', include(router_v1.urls)),
    path('recipes/download_shopping_cart/', download_shopping_cart),
    path('recipes/<ind:cart_id>/shopping_cart/', add_recipe_to_shopping_cart),
    path('recipes/<int:recipe_id>/favorite/', add_recipe_to_favorites),
]