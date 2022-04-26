from io import BytesIO

from django.db.models import Sum
from django.http import FileResponse
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


def add_recipe_to_favorite_or_shopping_cart(
    request, recipe_id, model, serializer, message_in, message_out
):
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
            obj = model.objects.get(user=user, recipe=recipe)
        except model.DoesNotExist:
            return Response(
                data={'errors': message_out},
                status=status.HTTP_400_BAD_REQUEST
            )
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    if model.objects.filter(user=user, recipe=recipe).exists():
        return Response(
            data={'errors': message_in},
            status=status.HTTP_400_BAD_REQUEST
        )
    serializer = serializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(user=user, recipe=recipe)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def add_recipe_to_favorites(request, recipe_id):
    add_recipe_to_favorite_or_shopping_cart(
        request, recipe_id, Favorite, FavoriteSerializer,
        RECIPE_ALREADY_IN_FAVORITES, RECIPE_NOT_IN_FAVORITES
    )


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def add_recipe_to_shopping_cart(request, recipe_id):
    add_recipe_to_favorite_or_shopping_cart(
        request, recipe_id, ShoppingCart, ShoppingCartSerializer,
        RECIPE_ALREADY_IN_SHOPPING_CART, RECIPE_NOT_IN_SHOPPING_CART
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_shopping_cart(request):
    shopping_cart = IngredientInRecipe.objects.filter(
        recipe__shopping_cart__author=request.user
    ).values(
        'ingredient__name', 'ingredient__measurement_unit'
    ).annotate(sum=Sum('amount'))
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    for unit in shopping_cart:
        string = '{} ({}) - {}'.format(
            unit.get('ingredient__name'),
            unit.get('sum'),
            unit.get('ingredient__measurement_unit'),
        )
    p.drawString(100, 100, string)
    p.showPage()
    p.save()
    buffer.seek(0)
    return FileResponse(
        buffer, as_attachment=True, filename='shopping_cart.pdf'
    )
