from django.core.validators import EmailValidator, MinLengthValidator

from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from users.models import MyUser, Subscriptions


MIN_PASSWORD_LENGTH = 8


class UserInfoSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField(
        method_name='get_sub'
    )

    class Meta:
        model = MyUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_sub(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Subscriptions.objects.filter(
                user=user, author=obj
            ).exists()
        return True


class CreateUserSerializer(UserCreateSerializer):
    email = serializers.EmailField(
        validators=[EmailValidator()]
    )
    password = serializers.CharField(
        validators=[MinLengthValidator(
            MIN_PASSWORD_LENGTH,
            message='Пароль должен быть не короче 8 символов!'),]
    )

    class Meta:
        model = MyUser
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
        user = MyUser.objects.create(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
