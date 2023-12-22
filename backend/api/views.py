import datetime
from http import HTTPStatus

from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, serializers
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from api.filters import RecipeFilter
from recipes.models import (
    Ingredient,
    Tag,
    Recipe,
    Follow,
    FavoriteRecipe,
    ShoppingCart,
    RecipeIngredient
)
from users.models import User
from .permissions import (
    IsAdminOrSuperuserOrReadOnly,
    IsAuthorStaffOrReadOnly
)
from .serializers import (
    IngredientSerializer,
    TagSerializer,
    RecipeSerializer,
    RecipeCreateSerializer,
    CheckFollowSerializer,
    AuthorSerializer,
    RecipeShortSerializer,
    FavoriteSerializer,
    ShoppingCartSerializer
)


class UserRetrieveViewSet(RetrieveModelMixin, GenericViewSet):
    queryset = User.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = (IsAuthenticated,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAdminOrSuperuserOrReadOnly,)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = [SearchFilter]
    search_fields = ['name']


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAdminOrSuperuserOrReadOnly,)
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = [
        'get',
        'post',
        'patch',
        'delete'
    ]

    def get_queryset(self):
        queryset = Recipe.objects.prefetch_related(
            'recipe_ingredients__ingredient',
            'tags'
        ).all()
        return queryset

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeSerializer

    @action(
        url_path='download_shopping_cart',
        detail=False,
        permission_classes=(IsAuthorStaffOrReadOnly,)
    )
    def download_shopping_cart(self, request):
        user = request.user
        cart_recipes = user.cart_recipes.all()
        recipes_names = ', '.join(
            [cart_recipe.recipe.name for cart_recipe in cart_recipes])
        ingredients_dict = (
            RecipeIngredient.objects.filter(recipe__recipe_cart__user=user)
            .values('ingredient__name', 'ingredient__measurement_unit').
            annotate(total_amount=Sum('amount')))
        ingredients_list = [
            (ingredient['ingredient__name'], str(ingredient['total_amount']),
             ingredient['ingredient__measurement_unit']) for
            ingredient in ingredients_dict]
        shoping_list = (f'Список: {user}: \n'
                        f'Для приготовления: {recipes_names}, '
                        f'возьмите:\n')
        for ingredient in ingredients_list:
            shoping_list += f'{" ".join(ingredient)}\n'
        shoping_list += (f'\nFoodgram\n'
                         f'{datetime.date.today()}')
        filename = 'list.txt'
        response = HttpResponse(
            shoping_list,
            content_type='text/plain'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class FollowViewSet(viewsets.ViewSet):
    permission_classes = (IsAuthorStaffOrReadOnly,)

    @action(
        methods=['POST'],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    @transaction.atomic()
    def create(self, request, id=None):
        user = request.user
        following = get_object_or_404(User, pk=id)
        data = {
            'user': user.id,
            'following': following.id,
        }
        serializer = CheckFollowSerializer(
            data=data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        Follow.objects.create(user=user, following=following)
        serializer = AuthorSerializer(following, context={'request': request})
        return Response(serializer.data, status=HTTPStatus.CREATED)

    @action(
        detail=True,
        methods=['DELETE'],
        permission_classes=(IsAuthorStaffOrReadOnly,)
    )
    @transaction.atomic()
    def destroy(self, request, id=None):
        user = request.user
        following = get_object_or_404(User, pk=id)
        data = {
            'user': user.id,
            'following': following.id,
        }
        serializer = CheckFollowSerializer(
            data=data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        follow = user.follows.filter(following=following)
        follow.delete()
        return Response(status=HTTPStatus.NO_CONTENT)

    @action(
        detail=False,
        permission_classes=(IsAuthorStaffOrReadOnly,)
    )
    def follows_list(self, request):
        user = request.user
        queryset = User.objects.filter(following__user=user)
        paginator = PageNumberPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = AuthorSerializer(
            paginated_queryset,
            many=True,
            context={'request': request}
        )
        return paginator.get_paginated_response(serializer.data)


class FavoriteViewSet(viewsets.ViewSet):

    @action(
        methods=['POST'],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    @transaction.atomic()
    def create(self, request, id=None):
        user = request.user
        recipe = get_object_or_404(Recipe, id=id)
        data = {
            'user': user.id,
            'recipe': recipe.id,
        }
        serializer = FavoriteSerializer(
            data=data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        FavoriteRecipe.objects.create(user=user, recipe=recipe)
        serializer = RecipeShortSerializer(
            recipe,
            context={'request': request}
        )
        return Response(
            serializer.data,
            status=HTTPStatus.CREATED,
            exception=True
        )

    @transaction.atomic()
    @action(
        methods=['POST'],
        detail=True,
        permission_classes=(IsAuthorStaffOrReadOnly,)
    )
    def destroy(self, request, id=None, ):
        user = request.user
        try:
            recipe = Recipe.objects.filter(pk=id).first()
        except Recipe.DoesNotExist:
            raise serializers.ValidationError('Рецепта нет')
        if not user.favorite_recipes.filter(recipe=recipe).first():
            raise serializers.ValidationError('Рецепт не в избранном')
        user.favorite_recipes.filter(recipe=recipe).delete()
        return Response(
            status=HTTPStatus.NO_CONTENT,
            exception=True
        )


class ShoppingCartViewSet(viewsets.ViewSet):

    @action(
        methods=['POST'],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    @transaction.atomic()
    def create(self, request, id=None):
        user = request.user
        recipe = get_object_or_404(Recipe, id=id)
        data = {
            'user': user.id,
            'recipe': recipe.id,
        }
        serializer = ShoppingCartSerializer(
            data=data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        ShoppingCart.objects.create(user=user, recipe=recipe)
        serializer = RecipeShortSerializer(
            recipe,
            context={'request': request}
        )
        return Response(
            serializer.data,
            status=HTTPStatus.CREATED,
            exception=True
        )

    @transaction.atomic()
    @action(
        methods=['POST'],
        detail=True,
        permission_classes=(IsAuthorStaffOrReadOnly,)
    )
    def destroy(self, request, id=None):
        user = request.user
        try:
            recipe = Recipe.objects.filter(pk=id).first()
        except Recipe.DoesNotExist:
            raise serializers.ValidationError('Рецепта нет')
        if not user.cart_recipes.filter(recipe=recipe).first():
            raise serializers.ValidationError('Рецепт не в корзине')
        user.cart_recipes.filter(recipe=recipe).delete()
        return Response(
            status=HTTPStatus.NO_CONTENT,
            exception=True
        )
