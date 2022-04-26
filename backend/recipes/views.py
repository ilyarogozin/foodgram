from io import BytesIO

from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from reportlab.pdfgen import canvas
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                     ShoppingCart, Tag)
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (FavoriteSerializer, IngredientSerializer,
                          RecipeSerializer, ShoppingCartSerializer,
                          TagSerializer)

RECIPE_ALREADY_IN_SHOPPING_CART = 'Рецепт уже в корзине!'
RECIPE_NOT_IN_SHOPPING_CART = 'Рецепта нет в корзине!'
RECIPE_ALREADY_IN_FAVORITES = 'Вы уже добавили рецепт в избранное!'
RECIPE_NOT_IN_FAVORITES = 'Рецепта нет в избранных!'
RECIPE_NOT_EXISTS = 'Рецепт не существует!'


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
    user = request.user
    try:
        recipe = Recipe.objects.get(pk=recipe_id)
    except Recipe.DoesNotExist:
        return Response(
            data={'errors': RECIPE_NOT_EXISTS},
            status=status.HTTP_400_BAD_REQUEST
        )
    if request.method == 'DELETE':
        try:
            favorite = Favorite.objects.get(user=user, recipe=recipe)
        except Favorite.DoesNotExist:
            return Response(
                data={'errors': RECIPE_NOT_IN_FAVORITES},
                status=status.HTTP_400_BAD_REQUEST
            )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    if Favorite.objects.filter(user=user, recipe=recipe).exists():
        return Response(
            data={'errors': RECIPE_ALREADY_IN_FAVORITES},
            status=status.HTTP_400_BAD_REQUEST
        )
    serializer = FavoriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(user=user, recipe=recipe)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def add_recipe_to_shopping_cart(request, recipe_id):
    user = request.user
    try:
        recipe = Recipe.objects.get(pk=recipe_id)
    except Recipe.DoesNotExist:
        return Response(
            data={'errors': RECIPE_NOT_EXISTS},
            status=status.HTTP_400_BAD_REQUEST
        )
    if request.method == 'DELETE':
        try:
            shopping_cart = ShoppingCart.objects.get(user=user, recipe=recipe)
        except ShoppingCart.DoesNotExist:
            return Response(
                data={'errors': RECIPE_NOT_IN_SHOPPING_CART},
                status=status.HTTP_400_BAD_REQUEST
            )
        shopping_cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
        return Response(
            data={'errors': RECIPE_ALREADY_IN_SHOPPING_CART},
            status=status.HTTP_400_BAD_REQUEST
        )
    serializer = ShoppingCartSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(user=user, recipe=recipe)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


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
