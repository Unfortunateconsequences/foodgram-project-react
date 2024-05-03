from django_filters import ModelMultipleChoiceFilter
from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe, Tag


class IngredientSearch(filters.FilterSet):
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_cart'
    )

    class Meta:
        fields = (
            'author',
            'tags',
            'is_favorited',
            'is_in_shopping_cart'
        )
        model = Recipe

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(favorite__user=self.request.user)
        return queryset

    def filter_is_in_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(cart__user=self.request.user)
        return queryset
