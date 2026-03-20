from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from .permissions import PublicAuthPermission
from .serializers import LoginSerializer, RegistrationSerializer


def get_safe_fullname(user):
    fullname = " ".join((user.fullname or "").strip().split())
    if not fullname:
        local_part = (user.email or "User").split("@")[0] or "User"
        return f"{local_part} User"
    if len(fullname.split(" ")) < 2:
        return f"{fullname} User"
    return fullname


class RegistrationView(generics.CreateAPIView):
    permission_classes = [PublicAuthPermission]
    authentication_classes = []
    serializer_class = RegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)

        response_data = {
            "token": token.key,
            "fullname": get_safe_fullname(user),
            "email": user.email,
            "user_id": user.id,
        }
        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)


class LoginView(generics.CreateAPIView):
    permission_classes = [PublicAuthPermission]
    authentication_classes = []
    serializer_class = LoginSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data["user"]

        token, _ = Token.objects.get_or_create(user=user)
        response_data = {
            "token": token.key,
            "fullname": get_safe_fullname(user),
            "email": user.email,
            "user_id": user.id,
        }
        return Response(response_data, status=status.HTTP_200_OK)
