from datetime import datetime, timedelta

from django.conf import settings

import environ
import redis
import requests
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

env = environ.Env(
    NGINX_URL=(str),
)

NGINX_URL = env("NGINX_URL")

BACKEND_PATH = "api/backend"

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
        response.set_cookie("access", access, secure=True, expires=datetime.now()+timedelta(minutes=5))

    if refresh:
        response.set_cookie("refresh", refresh, httponly=True, secure=True, expires=datetime.now()+timedelta(days=7))


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


def check_user_by_id(id):
    """
    Проверка существования пользователя по id.
    """
    url = f"{NGINX_URL}/{BACKEND_PATH}/users/exists/"
    params = {"user_id": id}
    response = requests.get(url, params=params, verify=False)

    if response.status_code == 200:
        data = response.json()
        user_id = data.get("user_id")
        return user_id

    return Response(response.json(), status=response.status_code)
