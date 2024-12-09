from django.conf import settings

import redis
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

redis_client = redis.StrictRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=1,
    decode_responses=True
)


def create_tokens(user_data):
    """
    Генерация токенов на основе данных пользователя.
    """
    refresh = RefreshToken()

    refresh["user_id"] = user_data["id"]
    refresh["username"] = user_data["username"]

    access = refresh.access_token

    return {
        "refresh": str(refresh),
        "access": str(access),
    }


def set_cookie(response: Response, access: str = None, refresh: str = None):
    """
    Устанвливает access и refresh токены в cookie.
    """
    if access:
        response.set_cookie("access", access, httponly=True, secure=True)

    if refresh:
        response.set_cookie("refresh", refresh, httponly=True, secure=True)


def is_token_blacklisted(token):
    """
    Проверка, находится ли токен в блэклисте.
    """
    return redis_client.sismember("blacklist_tokens", token)


def add_to_blacklist(token):
    """
    Добавление токена в блэклист.
    """
    redis_client.sadd("blacklist_tokens", token)
