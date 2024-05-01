from colorfield.fields import ColorField
from django.core.validators import MinValueValidator
from django.db import models

from users.models import FoodgramUser

MAX_LENGTH = 200
MIN_TIME = 1
MIN_AMOUNT = 1


class Tag(models.Model):

    name = models.CharField(
        verbose_name='Название тэга',
        unique=True,
        max_length=MAX_LENGTH
    )
    color = ColorField(
        default='#FF0000'
    )
    slug = models.SlugField(
        verbose_name='Уникальный идентификатор',
        unique=True,
        null=False
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):

    name = models.CharField(
        verbose_name='Название ингредиента',
        max_length=MAX_LENGTH
    )
    measurement_unit = models.CharField(
        verbose_name='Единицы измерения',
        max_length=MAX_LENGTH
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):

    author = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта',
    )
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=MAX_LENGTH
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='recipes/'
    )
    text = models.TextField(
        verbose_name='Текст рецепта',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиаенты',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Тэги рецепта',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=[
            MinValueValidator(
                MIN_TIME,
                message='Время приготовления не может быть меньше минуты')
        ]
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class TagRecipe(models.Model):
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тэг',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Тэг рецепта'
        verbose_name_plural = 'Тэги рецептов'
        constraints = (
            models.UniqueConstraint(
                fields=['tag', 'recipe'],
                name='unique_tag_recipe'
            ),
        )

    def __str__(self):
        return f'{self.recipe} присвоен тег {self.tag}.'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )

    amount = models.PositiveSmallIntegerField(
        verbose_name='',
        validators=[
            MinValueValidator(
                MIN_AMOUNT,
                message='Количество должно быть больше 1')
        ]
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = (
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            ),
        )

    def __str__(self):
        return (
            f'{self.ingredient.name}:'
            f'{self.amount} {self.ingredient.measurement_unit}'
        )


class Favorite(models.Model):

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    user = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='favorite_recipes'),
        ]

        def __str__(self):
            return f'{self.recipe} теперь в избранном {self.user}'


class Cart(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт в корзине'
    )
    user = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_recipe_in_cart'
            ),
        ]

        def __str__(self):
            return f'{self.user} добавил {self.recipe} в корзину'
