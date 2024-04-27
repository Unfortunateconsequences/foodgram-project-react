from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from api.pagination import LimitNumberPagination
from api.serializers import SubscriptionSerializer

from users.models import MyUser, Subscriptions
from users.serializers import UserInfoSerializer, CreateUserSerializer


class CustomUserViewSet(UserViewSet):
    queryset = MyUser.objects.all()
    pagination_class = LimitNumberPagination
    permission_classes = (AllowAny,)

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateUserSerializer
        return UserInfoSerializer

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = [IsAuthenticated,]
        elif self.action == 'set_password':
            self.permission_classes = [IsAuthenticated,]
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
        author = get_object_or_404(MyUser, pk=id)

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
        subscription = Subscriptions.objects.filter(
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
        if self.request.user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        user = self.request.user
        subscriptions = Subscriptions.objects.filter(user=user)
        paginator = LimitNumberPagination()
        result_page = paginator.paginate_queryset(subscriptions, request)
        serializer = SubscriptionSerializer(
            result_page,
            many=True,
            context={'request': request}
        )

        return paginator.get_paginated_response(serializer.data)
