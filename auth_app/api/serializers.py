from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from rest_framework import serializers

User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    repeated_password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["fullname", "email", "password", "repeated_password"]
        extra_kwargs = {
            "password": {"write_only": True, "min_length": 8},
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already registered.")
        return value

    def validate_fullname(self, value):
        normalized = " ".join((value or "").strip().split())
        if len(normalized.split(" ")) < 2:
            raise serializers.ValidationError(
                "Fullname must contain at least first and last name.")
        return normalized

    def validate(self, attrs):
        if attrs["password"] != attrs["repeated_password"]:
            raise serializers.ValidationError(
                {"repeated_password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("repeated_password")
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            fullname=validated_data["fullname"],
        )
        return user


class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = ["email", "password"]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password,
        )

        if user is None:
            raise serializers.ValidationError(
                {"detail": "Invalid credentials."})

        attrs["user"] = user
        return attrs
