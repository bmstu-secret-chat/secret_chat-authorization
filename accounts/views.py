import environ
import requests
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from .utils import add_to_blacklist, check_user_by_id, create_tokens, is_token_blacklisted, set_cookie

env = environ.Env(
    NGINX_URL=(str),
)

NGINX_URL = env("NGINX_URL")

BACKEND_PATH = "api/backend"


@api_view(['POST'])
def signup_view(request):
    """
    Регистрация пользователя.
    """
    url = f"{NGINX_URL}/{BACKEND_PATH}/users/create/"
    response = requests.post(url, json=request.data, verify=False)

    if response.status_code == 201:
        data = response.json()
        user_data = data.get("user")
        tokens = create_tokens(user_data)

        response = Response({"user_id": user_data["id"]}, status=status.HTTP_201_CREATED)
        set_cookie(response, tokens["access"], tokens["refresh"])
        return response

    return Response(response.json(), status=response.status_code)


@api_view(['POST'])
def login_view(request):
    """
    Логинит пользователя и устанавливает JWT токены в куки.
    """
    url = f"{NGINX_URL}/{BACKEND_PATH}/users/check/"
    response = requests.post(url, data=request.data, verify=False)

    if response.status_code == 200:
        data = response.json()
        user_data = data.get("user")
        tokens = create_tokens(user_data)

        response = Response({"user_id": user_data["id"]}, status=status.HTTP_200_OK)
        set_cookie(response, tokens["access"], tokens["refresh"])
        return response

    return Response(response.json(), status=response.status_code)


@api_view(['POST'])
def logout_view(request):
    """
    Выход пользователя.
    """
    refresh_token = request.COOKIES.get("refresh")

    if refresh_token:
        add_to_blacklist(refresh_token)

    response = Response({}, status=status.HTTP_200_OK)
    response.delete_cookie("access")
    response.delete_cookie("refresh")
    return response


@api_view(['GET'])
def check_view(request):
    """
    Проверяет токен и определяет пользователя.
    """
    access_token = request.COOKIES.get("access")

    if not access_token:
        return Response({"error": "Access токен не предоставлен"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        token = AccessToken(access_token)
        user_id = token["user_id"]
        user_check = check_user_by_id(user_id)

        if not user_check:
            return Response({"error": "Пользователя с таким id не существует"}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({"id": user_id}, status=status.HTTP_200_OK)

    except TokenError:
        return Response({"error": "Неверный access токен"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
def refresh_view(request):
    refresh_token = request.COOKIES.get("refresh")

    if not refresh_token:
        return Response({"error": "Refresh токен не предоставлен"}, status=status.HTTP_401_UNAUTHORIZED)

    if is_token_blacklisted(refresh_token):
        return Response({"error": "Refresh токен в блэклисте"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        refresh = RefreshToken(refresh_token)
    except TokenError:
        return Response({"error": "Refresh токен недействителен или истек"}, status=status.HTTP_401_UNAUTHORIZED)

    user_id = refresh["user_id"]
    username = refresh["username"]
    user_data = {"id": user_id, "username": username}
    tokens = create_tokens(user_data)

    add_to_blacklist(refresh_token)

    response = Response({}, status=status.HTTP_200_OK)
    set_cookie(response, tokens["access"], tokens["refresh"])

    return response
