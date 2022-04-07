from django.shortcuts import get_object_or_404
from djoser.serializers import SetPasswordSerializer
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from .models import Subscription, User
from .serializers import (SubscriptionSerializer, UserCreateSerializer,
                          UserSerializer)

SUBSCRIBE_TO_YOURSELF = 'Вы не можете подписаться на себя.'
SUBSCRIPTION_DOES_NOT_EXIST = 'Подписка не существует.'
SUBSCRIPTION_ALREADY_EXISTS = 'Подписка уже существует.'


class UserViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                  mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()

    def get_permissions(self):
        if self.action == 'create' or self.action == 'list':
            return (AllowAny(),)
        return (IsAuthenticated(),)

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action == 'set_password':
            return SetPasswordSerializer
        if self.action == 'subscribe' or self.action == 'subscriptions':
            return SubscriptionSerializer
        return UserSerializer

    @action(methods=['GET'], detail=False)
    def me(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(methods=['POST'], detail=False)
    def set_password(self, request):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(
            serializer.validated_data.get('new_password')
        )
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['POST', 'DELETE'], detail=False,
            url_path=r'(?P<id>\d+)/subscribe')
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(User, id=id)
        if user == author:
            raise ValidationError(SUBSCRIBE_TO_YOURSELF)
        if request.method == 'DELETE':
            try:
                subscription = Subscription.objects.get(
                    user=user, author=author
                )
            except Subscription.DoesNotExist:
                raise ValidationError(SUBSCRIPTION_DOES_NOT_EXIST)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        if Subscription.objects.filter(user=user, author=author).exists():
            raise ValidationError(SUBSCRIPTION_ALREADY_EXISTS)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user, author=author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['GET'], detail=False)
    def subscriptions(self, request):
        subs = Subscription.objects.filter(user=request.user)
        page = self.paginate_queryset(subs)
        serializer = self.get_serializer(subs, many=True)
        if page:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK)
