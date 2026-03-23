"""Authentication API views for registration and login."""

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny

from .serializers import LoginSerializer, RegistrationSerializer


def get_safe_fullname(user):
    """Return normalized fullname or fallback generated from email."""
    fullname = " ".join((user.fullname or "").strip().split())
    if not fullname:
        local_part = (user.email or "User").split("@")[0] or "User"
        return f"{local_part} User"
    if len(fullname.split(" ")) < 2:
        return f"{fullname} User"
    return fullname


class RegistrationView(generics.CreateAPIView):
    """Create user account and issue an authentication token."""

    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = RegistrationSerializer

    def _build_auth_response(self, user):
        """Build token response payload for authenticated user."""
        token, _ = Token.objects.get_or_create(user=user)
        return {
            "token": token.key,
            "fullname": get_safe_fullname(user),
            "email": user.email,
            "user_id": user.id,
        }

    def create(self, request, *args, **kwargs):
        """Register a user and return token plus profile summary."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        response_data = self._build_auth_response(user)
        headers = self.get_success_headers(serializer.data)
        return Response(
            response_data, 
            status=status.HTTP_201_CREATED, 
            headers=headers
            )


class LoginView(generics.CreateAPIView):
    """Authenticate user and return authentication token."""

    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = LoginSerializer

    def _build_login_response(self, user):
        """Build the login response payload for authenticated user."""
        token, _ = Token.objects.get_or_create(user=user)
        return {
            "token": token.key,
            "fullname": get_safe_fullname(user),
            "email": user.email,
            "user_id": user.id,
        }

    def create(self, request, *args, **kwargs):
        """Validate credentials and return token-based login response."""
        serializer = self.get_serializer(
            data=request.data, 
            context={"request": request}
            )
        if not serializer.is_valid():
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
                )

        user = serializer.validated_data["user"]
        response_data = self._build_login_response(user)
        return Response(response_data, status=status.HTTP_200_OK)
