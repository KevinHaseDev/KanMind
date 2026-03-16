from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Comment, Task


User = get_user_model()


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "fullname"]


class TaskSerializer(serializers.ModelSerializer):
    assignee = serializers.SerializerMethodField(read_only=True)
    assignee_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    reviewer = UserSummarySerializer(read_only=True)
    reviewer_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    due_date = serializers.DateTimeField(format="%Y-%m-%d", input_formats=["%Y-%m-%d", "iso-8601"])
    comments_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "board",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "assignee_id",
            "reviewer",
            "reviewer_id",
            "due_date",
            "comments_count",
        ]

    def get_assignee(self, obj):
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            user = obj.assignies.filter(id=request.user.id).first()
            if user:
                return UserSummarySerializer(user).data

        user = obj.assignies.order_by("id").first()
        if not user:
            return None
        return UserSummarySerializer(user).data

    def validate_assignee_id(self, value):
        if value is None:
            return value
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid assignee user id.")
        return value

    def validate_reviewer_id(self, value):
        if value is None:
            return value
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid reviewer user id.")
        return value

    def create(self, validated_data):
        assignee_id = validated_data.pop("assignee_id", None)
        reviewer_id = validated_data.pop("reviewer_id", None)

        if reviewer_id is not None:
            validated_data["reviewer_id"] = reviewer_id

        task = Task.objects.create(**validated_data)

        if assignee_id is not None:
            task.assignies.set([assignee_id])

        return task

    def update(self, instance, validated_data):
        assignee_id = validated_data.pop("assignee_id", serializers.empty)
        reviewer_id = validated_data.pop("reviewer_id", serializers.empty)

        if reviewer_id is not serializers.empty:
            instance.reviewer_id = reviewer_id

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if assignee_id is not serializers.empty:
            if assignee_id is None:
                instance.assignies.clear()
            else:
                instance.assignies.set([assignee_id])

        return instance


class CommentSerializer(serializers.ModelSerializer):
    author = UserSummarySerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "content", "author", "created_at"]
        read_only_fields = ["id", "author", "created_at"]
