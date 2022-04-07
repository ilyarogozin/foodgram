from io import BytesIO

from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from reportlab.pdfgen import canvas
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Ingredient, IngredientInRecipe, Recipe, Tag
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import IngredientSerializer, TagSerializer, RecipeSerializer

RECIPE_ALREADY_IN_SHOPPING_CART = 'Этот рецепт уже у вас в корзине.'
RECIPE_ALREADY_IN_FAVORITES = 'Этот рецепт уже у вас в избранных.'


class IngredientViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class TagViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin,
                 viewsets.GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrAdminOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def add_recipe_to_favorites(request, recipe_id):
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    user = request.user
    if request.method == 'DELETE':
        user.favorites.remove(recipe)
        return Response(status=status.HTTP_204_NO_CONTENT)
    if recipe.id in request.user.favorites.values_list('id', flat=True):
        return Response(
            data={'errors': RECIPE_ALREADY_IN_FAVORITES},
            status=status.HTTP_400_BAD_REQUEST
        )
    user.favorites.add(recipe)
    data = {
        'id': recipe.id,
        'name': recipe.name,
        'image': recipe.image,
        'cooking_time': recipe.cooking_time
    }
    return Response(data=data, status=status.HTTP_201_CREATED)


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def add_recipe_to_shopping_cart(request, recipe_id):
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    user = request.user
    if request.method == 'DELETE':
        user.favorites.remove(recipe)
        return Response(status=status.HTTP_204_NO_CONTENT)
    if recipe.id in request.user.favorites.values_list('id', flat=True):
        return Response(
            data={'errors': RECIPE_ALREADY_IN_SHOPPING_CART},
            status=status.HTTP_400_BAD_REQUEST
        )
    user.favorites.add(recipe)
    data = {
        'id': recipe.id,
        'name': recipe.name,
        'image': recipe.image,
        'cooking_time': recipe.cooking_time
    }
    return Response(data=data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_shopping_cart(request):
    shopping_cart = IngredientInRecipe.objects.filter(
        recipe__shopping_cart__author=request.user
    ).values(
        'ingredient__name', 'ingredient__measurement_unit'
    ).annotate(amount=Sum('amount'))
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    for unit in shopping_cart:
        string = '{} ({}) - {}'.format(
            unit.get('ingredient__name'),
            unit.get('amount'),
            unit.get('ingredient__measurement_unit'),
        )
    p.drawString(100, 100, string)
    p.showPage()
    p.save()
    buffer.seek(0)
    return FileResponse(
        buffer, as_attachment=True, filename='shopping_cart.pdf'
    )
