from datetime import datetime, timedelta

from django.conf import settings

import environ
import redis
import requests
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

env = environ.Env()

INTERNAL_SECRET_KEY = env("INTERNAL_SECRET_KEY")

NGINX_URL = env("NGINX_URL")

BACKEND_PATH = "api/backend"

REALTIME_PATH = "api/realtime"

redis_client = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=1, decode_responses=True)


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
        user = data.get("user")
        return user

    return Response(response.json(), status=response.status_code)


def get_private_key(user_id):
    """
    Получение приватного ключа пользователя.
    """
    url = f"{NGINX_URL}/{REALTIME_PATH}/messenger/private-key/"
    headers = {"X-Internal-Secret": INTERNAL_SECRET_KEY}
    params = {"user_id": user_id}
    response = requests.get(url, headers=headers, params=params, verify=False)

    if response.status_code == 200:
        data = response.json()
        private_key = data.get("private_key")
        return private_key

    return {"error": response.json(), "status": response.status_code}


def update_count_auth(user_id, action):
    """
    Обновление счётчика авторизаций.
    """
    url = f"{NGINX_URL}/{BACKEND_PATH}/users/count-auth/"
    headers = {"X-Internal-Secret": INTERNAL_SECRET_KEY}
    data = {"user_id": user_id, "action": action}
    requests.patch(url, headers=headers, data=data, verify=False)
