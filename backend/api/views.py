from django.db import IntegrityError
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAdminUser, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.cart import shopping_cart_pdf
from api.filters import IngredientSearch, RecipeFilter
from api.pagination import LimitNumberPagination
from api.permissions import IsOwnerOrReadOnly, ReadOnly
from api.serializers import (CartSerializer, FavoritesSerializer,
                             IngredientSerializer, RecipeCreateSerializer,
                             RecipeIntroSerializer, RecipeSerializer,
                             SubscriptionSerializer, TagSerializer)
from recipes.models import (Cart, Favorite, Ingredient, Recipe,
                            RecipeIngredient, Tag)
from users.models import FoodgramUser, Subscription
from .serializers import CreateUserSerializer, UserInfoSerializer


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_class = [IsAdminUser | ReadOnly]
    pagination_class = None


class IngredientViewSet(ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAdminUser | ReadOnly]
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_class = IngredientSearch


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = LimitNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    ordering_fields = ('pub_date',)
    ordering = ('pub_date',)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateSerializer
        elif self.action in ('favorite', 'shopping_cart'):
            return RecipeIntroSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticatedOrReadOnly(), ]
        elif self.action in ('update', 'partial_update',
                             'destroy', 'download_shopping_cart'):
            return [IsOwnerOrReadOnly(), ]
        elif self.action in ('favorite', 'shopping_cart'):
            return [IsAuthenticated(), ]
        return [AllowAny(), ]

    def add_item(self, model, serializer, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        try:
            item = model.objects.create(recipe=recipe, user=request.user)
            serializer = serializer(item)
        except IntegrityError:
            return Response(
                {'message': 'Рецепт уже добавлен'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)

    def delete_item(self, model, request, pk=None):
        try:
            item = model.objects.get(recipe=pk, user=request.user)
            item.delete()
        except model.DoesNotExist:
            return Response(
                {'message': 'Невозможно удалить, этого рецепта нет в списке'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=True)
    def favorite(self, request, pk=None):
        return self.add_item(Favorite, FavoritesSerializer, request, pk)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        return self.delete_item(Favorite, request, pk)

    @action(methods=['post'], detail=True)
    def shopping_cart(self, request, pk=None):
        return self.add_item(Cart, CartSerializer, request, pk)

    @shopping_cart.mapping.delete
    def shopping_cart_del(self, request, pk=None):
        return self.delete_item(Cart, request, pk)

    @action(methods=['get'], detail=False)
    def download_shopping_cart(self, request):
        user = request.user
        recipes = Recipe.objects.filter(cart__user=user)
        shopping_list = (
            RecipeIngredient.objects.filter(recipe__in=recipes)
            .values('ingredient')
            .annotate(total_amount=Sum('amount'))
        )
        response = shopping_cart_pdf(shopping_list)
        return response


class CustomUserViewSet(UserViewSet):
    queryset = FoodgramUser.objects.all()
    pagination_class = LimitNumberPagination
    permission_classes = (AllowAny,)

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateUserSerializer
        return UserInfoSerializer

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = [IsAuthenticated, ]
        elif self.action == 'set_password':
            self.permission_classes = [IsAuthenticated, ]
        return super().get_permissions()

    @action(detail=False, methods=['post'])
    def set_password(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        if user.check_password(current_password):
            user.set_password(new_password)
            user.save()
            return Response({'message': 'Пароль успешно изменен.'})
        return Response(
            {'message': 'Текущий пароль неверный.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id):
        author = get_object_or_404(FoodgramUser, pk=id)

        if request.method == 'POST':
            try:
                serializer = SubscriptionSerializer(
                    data={'user': request.user.pk, 'author': author.pk},
                    context={'request': request},
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
            except IntegrityError:
                return Response(
                    {'message': 'Вы уже подписаны!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        subscription = Subscription.objects.filter(
            user=request.user,
            author=author
        )

        if subscription.exists():
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {'message': 'Вы не были подписаны ранее!'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(methods=['get'], detail=False,
            permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        user = self.request.user
        subscriptions = Subscription.objects.filter(user=user)
        paginator = LimitNumberPagination()
        result_page = paginator.paginate_queryset(subscriptions, request)
        serializer = SubscriptionSerializer(
            result_page,
            many=True,
            context={'request': request}
        )

        return paginator.get_paginated_response(serializer.data)
