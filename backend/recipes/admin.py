from django.contrib import admin
from django.db.models import Count
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from recipes.models import (Cart, Favorites, Ingredient, Recipe,
                            RecipeIngredient, Tag, TagRecipe)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')


class RecipeIngredientsInLine(admin.TabularInline):
    model = Recipe.ingredients.through
    min_num = 1
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'count_favorites')
    list_filter = ('author', 'name', 'tags')
    filter_horizontal = ('tags',)
    inlines = (RecipeIngredientsInLine,)

    def count_favorites(self, obj):
        return obj.favorites_count

    count_favorites.short_description = 'Added to favorites'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(favorites_count=Count('favorites'))
        return queryset


class IngredientResourse(resources.ModelResource):
    class Meta:
        model = Ingredient


@admin.register(Ingredient)
class IngredientAdmin(ImportExportModelAdmin):
    resource_class = IngredientResourse
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)


@admin.register(TagRecipe)
class TagRecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'tag')


@admin.register(Favorites)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'user')


admin.site.register(RecipeIngredient)
admin.site.register(Cart)
