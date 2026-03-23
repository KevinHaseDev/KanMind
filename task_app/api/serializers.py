"""Serializers for task and comment API endpoints."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from ..models import Comment, Task

User = get_user_model()


class UserSummarySerializer(serializers.ModelSerializer):
    """Compact user representation used in task responses."""

    class Meta:
        model = User
        fields = ["id", "email", "fullname"]


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for creating, updating, and listing tasks."""

    ALLOWED_STATUSES = {"to-do", "in-progress", "review", "done"}
    ALLOWED_PRIORITIES = {"low", "medium", "high"}
    ASSIGNEE_MEMBER_ERROR = "Assignee must be a member of the board."
    REVIEWER_MEMBER_ERROR = "Reviewer must be a member of the board."

    assignee = serializers.SerializerMethodField(read_only=True)
    assignee_id = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True,
    )
    reviewer = UserSummarySerializer(read_only=True)
    reviewer_id = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True,
    )
    due_date = serializers.DateTimeField(
        format="%Y-%m-%d",
        input_formats=["%Y-%m-%d", "iso-8601"],
    )
    comments_count = serializers.SerializerMethodField(read_only=True)

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
        read_only_fields = ["id", "comments_count"]

    def get_assignee(self, obj):
        """Return current user assignee first, otherwise first assignee."""
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            user = obj.assignees.filter(id=request.user.id).first()
            if user:
                return UserSummarySerializer(user).data

        user = obj.assignees.order_by("id").first()
        if not user:
            return None
        return UserSummarySerializer(user).data

    def get_comments_count(self, obj):
        """Return annotated comments count or fallback DB count."""
        if hasattr(obj, "comments_count"):
            return obj.comments_count
        return obj.comments.count()

    def validate_status(self, value):
        """Validate task status against allowed values."""
        if value not in self.ALLOWED_STATUSES:
            raise serializers.ValidationError(
                "Status must be one of: to-do, in-progress, review, done."
            )
        return value

    def validate_priority(self, value):
        """Validate task priority against allowed values."""
        if value not in self.ALLOWED_PRIORITIES:
            raise serializers.ValidationError("Priority must be one of: low, medium, high.")
        return value

    def validate_assignee_id(self, value):
        """Validate assignee id if provided."""
        if value is None:
            return value
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid assignee user id.")
        return value

    def validate_reviewer_id(self, value):
        """Validate reviewer id if provided."""
        if value is None:
            return value
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid reviewer user id.")
        return value

    def _validate_member_id(self, board, user_id, field_name, message):
        """Validate that the provided user id belongs to board members."""
        if board is None or user_id in (serializers.empty, None):
            return
        if not board.members.filter(id=user_id).exists():
            raise serializers.ValidationError({field_name: message})

    def _member_validation_values(self, attrs):
        """Return board, assignee id, and reviewer id for validation."""
        board = attrs.get("board") or getattr(self.instance, "board", None)
        assignee_id = attrs.get("assignee_id", serializers.empty)
        reviewer_id = attrs.get("reviewer_id", serializers.empty)
        return board, assignee_id, reviewer_id

    def validate(self, attrs):
        """Validate membership rules for assignee and reviewer."""
        board, assignee_id, reviewer_id = self._member_validation_values(attrs)
        self._validate_member_id(board, assignee_id, "assignee_id", self.ASSIGNEE_MEMBER_ERROR)
        self._validate_member_id(board, reviewer_id, "reviewer_id", self.REVIEWER_MEMBER_ERROR)
        return attrs

    def create(self, validated_data):
        """Create task and assign optional reviewer and assignee."""
        assignee_id = validated_data.pop("assignee_id", None)
        reviewer_id = validated_data.pop("reviewer_id", None)

        if reviewer_id is not None:
            validated_data["reviewer_id"] = reviewer_id

        task = Task.objects.create(**validated_data)

        if assignee_id is not None:
            task.assignees.set([assignee_id])

        return task

    def _apply_reviewer(self, instance, reviewer_id):
        """Apply reviewer id when reviewer was explicitly provided."""
        if reviewer_id is not serializers.empty:
            instance.reviewer_id = reviewer_id

    def _apply_field_updates(self, instance, validated_data):
        """Apply all scalar field updates to the instance."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

    def _apply_assignee(self, instance, assignee_id):
        """Apply assignee update behavior for null, set, or unchanged."""
        if assignee_id is serializers.empty:
            return
        if assignee_id is None:
            instance.assignees.clear()
            return
        instance.assignees.set([assignee_id])

    def update(self, instance, validated_data):
        """Update task including reviewer and assignee relation handling."""
        assignee_id = validated_data.pop("assignee_id", serializers.empty)
        reviewer_id = validated_data.pop("reviewer_id", serializers.empty)

        self._apply_reviewer(instance, reviewer_id)
        self._apply_field_updates(instance, validated_data)
        self._apply_assignee(instance, assignee_id)
        return instance


class CommentSerializer(serializers.ModelSerializer):
    """Serializer used for comment creation responses."""

    author = UserSummarySerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "content", "author", "created_at"]
        read_only_fields = ["id", "author", "created_at"]


class CommentListSerializer(serializers.ModelSerializer):
    """Serializer used for listing task comments."""

    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["id", "created_at", "author", "content"]

    def get_author(self, obj):
        """Return comment author full name."""
        return obj.author.fullname


class TaskUpdateResponseSerializer(serializers.ModelSerializer):
    """Serializer for task patch response payloads."""

    assignee = serializers.SerializerMethodField(read_only=True)
    reviewer = UserSummarySerializer(read_only=True)
    due_date = serializers.DateTimeField(format="%Y-%m-%d")

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "reviewer",
            "due_date",
        ]

    def get_assignee(self, obj):
        """Return first assignee as user summary or null."""
        user = obj.assignees.order_by("id").first()
        if not user:
            return None
        return UserSummarySerializer(user).data
