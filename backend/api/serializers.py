from django.core.validators import EmailValidator, MinLengthValidator
from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Cart, Favorite, Ingredient, Recipe,
                            RecipeIngredient, Tag)
from users.models import FoodgramUser, Subscription

MIN_PASSWORD_LENGTH = 8


class UserInfoSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = FoodgramUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subcribed(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Subscription.objects.filter(
                user=user, author=obj
            ).exists()
        return False


class CreateUserSerializer(UserCreateSerializer):
    email = serializers.EmailField(
        validators=[EmailValidator()]
    )
    password = serializers.CharField(
        validators=[MinLengthValidator(
            MIN_PASSWORD_LENGTH,
            message='Пароль должен быть не короче 8 символов!'), ]
    )

    class Meta:
        model = FoodgramUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password'
        )
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = FoodgramUser.objects.create(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        fields = (
            'id',
            'name',
            'color',
            'slug'
        )
        model = Tag
        lookup_field = 'slug'


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        fields = (
            'id',
            'name',
            'measurement_unit'
        )
        model = Ingredient


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.CharField(
        source='ingredient.id'
    )
    name = serializers.CharField(
        source='ingredient.name'
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )
        model = RecipeIngredient


class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    tags = TagSerializer(
        many=True,
        read_only=True
    )
    author = UserInfoSerializer(
        read_only=True
    )
    ingredients = RecipeIngredientSerializer(
        source='recipeingredient_set',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        model = Recipe

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        user = request.user
        return (
            user.is_authenticated
            and Favorite.objects.filter(
                recipe=obj,
                user=user
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        user = request.user
        return (
            user.is_anonymous
            or Cart.objects.filter(
                recipe=obj,
                user=user
            ).exists()
        )


class RecipeIntroSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
        model = Recipe


class FavoritesSerializer(serializers.ModelSerializer):

    class Meta:
        fields = (
            'user',
            'recipe'
        )
        model = Favorite
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже есть в избранном',
            )
        ]

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeIntroSerializer(instance.recipe, context=context).data


class CartSerializer(serializers.ModelSerializer):

    class Meta:
        fields = (
            'user',
            'recipe'
        )
        model = Cart
        validators = [
            UniqueTogetherValidator(
                queryset=Cart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже есть в корзине'
            )
        ]

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeIntroSerializer(instance.recipe, context=context).data


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(write_only=True)
    amount = serializers.IntegerField(write_only=True)

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'amount',
        )

    def validate_amount(self, amount):
        if amount == 0:
            raise serializers.ValidationError('Количество не может быть 0')
        return amount


class RecipeCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        fields = ('id',
                  'ingredients',
                  'tags',
                  'image',
                  'name',
                  'text',
                  'cooking_time'
                  )
        model = Recipe

    def validate(self, data):
        tags = data.get('tags')
        ingredients = data.get('ingredients')
        cooking_time = data.get('cooking_time')

        if not tags:
            raise serializers.ValidationError('Укажите тэг')
        if not ingredients:
            raise serializers.ValidationError('Укажите ингридиенты')
        if cooking_time < 1:
            raise serializers.ValidationError(
                'Время приготовления не может быть меньше 1 минуты'
            )

        unique_ingredients = set()
        duplicate_ingredients = []

        for ingredient in ingredients:
            if ingredient['id'] in unique_ingredients:
                duplicate_ingredients.append(ingredient['id'])
            else:
                unique_ingredients.add(ingredient['id'])

        if duplicate_ingredients:
            raise serializers.ValidationError(
                f'Ингредиент {duplicate_ingredients} уже есть в списке, '
                f'если в рецепте он используется дважды, '
                f'увеличьте количество уже добавленного ингредиента'
            )
        return data

    @staticmethod
    def create_ingredients(recipe, ingredients):
        recipe_ingredients = []
        for ingredient in ingredients:
            recipe_ingredients.append(
                RecipeIngredient(
                    ingredient_id=ingredient.get('id'),
                    amount=ingredient['amount'],
                    recipe=recipe,
                )
            )
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance = super().update(instance, validated_data)
        RecipeIngredient.objects.filter(recipe=instance).delete()
        self.create_ingredients(instance, ingredients)
        instance.tags.set(tags, clear=True)
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeSerializer(instance, context=context).data


class SubscriptionGetSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = RecipeIntroSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = FoodgramUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (request.user.is_authenticated or Subscription.objects.filter(
            user=request.user, author=obj.id).exists())

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = ('user', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны!',
            )
        ]

    def validate(self, data):
        author = data.get('author')
        user = self.context.get('request').user

        if user == author:
            raise serializers.ValidationError('Нельзя подписаться на себя.')

        return data

    def to_representation(self, instance):
        return SubscriptionGetSerializer(
            instance.author, context={'request': self.context.get('request')}
        ).data
