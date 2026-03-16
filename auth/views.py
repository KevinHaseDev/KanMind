from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token

from .serializers import LoginSerializer, RegistrationSerializer


class RegistrationView(APIView):
	permission_classes = []
	authentication_classes = []

	def post(self, request):
		serializer = RegistrationSerializer(data=request.data)
		if not serializer.is_valid():
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

		user = serializer.save()
		token, _ = Token.objects.get_or_create(user=user)

		response_data = {
			"token": token.key,
			"fullname": user.fullname,
			"email": user.email,
			"user_id": user.id,
		}
		return Response(response_data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
	permission_classes = []
	authentication_classes = []

	def post(self, request):
		serializer = LoginSerializer(data=request.data, context={"request": request})
		if not serializer.is_valid():
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

		user = serializer.validated_data["user"]

		token, _ = Token.objects.get_or_create(user=user)
		response_data = {
			"token": token.key,
			"fullname": user.fullname,
			"email": user.email,
			"user_id": user.id,
		}
		return Response(response_data, status=status.HTTP_200_OK)
