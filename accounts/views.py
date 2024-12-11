import environ
import requests
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from .utils import add_to_blacklist, create_tokens, is_token_blacklisted, set_cookie

env = environ.Env(
    BACKEND_URL=(str),
)

BACKEND_URL = env("BACKEND_URL")


@api_view(['POST'])
def signup_view(request):
    """
    Регистрация пользователя.
    """
    url = f"{BACKEND_URL}/api/users/create/"
    response = requests.post(url, json=request.data)

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
    url = f"{BACKEND_URL}/api/users/check/"
    response = requests.post(url, data=request.data)

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
    access_token = request.COOKIES.get("access")
    refresh_token = request.COOKIES.get("refresh")

    if access_token:
        add_to_blacklist(access_token)
    if refresh_token:
        add_to_blacklist(refresh_token)

    response = Response({}, status=status.HTTP_200_OK)
    response.delete_cookie("access")
    response.delete_cookie("refresh")
    return response


@api_view(['GET'])
def check_view(request):
    """
    Проверяет токены и определяет пользователя.
    """
    access_token = request.COOKIES.get("access")
    refresh_token = request.COOKIES.get("refresh")

    if not access_token:
        return Response({"error": "Access токен не предоставлен"}, status=status.HTTP_401_UNAUTHORIZED)

    if is_token_blacklisted(access_token):
        return Response({"error": "Access токен в блэклисте"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        token = AccessToken(access_token)
        user_id = token["user_id"]
        return Response({"user_id": user_id}, status=status.HTTP_200_OK)

    except TokenError:
        if not refresh_token:
            return Response({"error": "Refresh токен не предоставлен"}, status=status.HTTP_401_UNAUTHORIZED)

        if is_token_blacklisted(refresh_token):
            return Response({"error": "Refresh токен в блэклисте"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            refresh = RefreshToken(refresh_token)
            new_access_token = refresh.access_token

            response = Response({"user_id": refresh["user_id"]})
            set_cookie(response, str(new_access_token))
            return response

        except TokenError:
            return Response({"error": "Недопустимый refresh токен"}, status=status.HTTP_401_UNAUTHORIZED)
