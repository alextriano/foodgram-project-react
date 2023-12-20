import django_filters
from django_filters import FilterSet, filters, widgets

from recipes.models import (
    Recipe,
    Tag,
    User
)


class RecipeFilter(FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug',
    )
    is_favorited = filters.BooleanFilter(
        widget=widgets.BooleanWidget(),
        method='filter_is_favorited'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        widget=widgets.BooleanWidget(),
        method='filter_is_in_shopping_cart'
    )
    author = filters.ModelChoiceFilter(queryset=User.objects.all())

    class Meta:
        model = Recipe
        fields = [
            'tags__slug',
            'is_favorited',
            'is_in_shopping_cart',
            'author'
        ]

    def filter_is_favorited(self, queryset, name, value):
        if value:
            return queryset.filter(recipe_favorites__user=self.request.user)
        else:
            return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(recipe_cart__user=self.request.user)
        else:
            return queryset
