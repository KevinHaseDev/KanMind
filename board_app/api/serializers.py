from django.contrib.auth import get_user_model
from rest_framework import serializers

from ..models import Board
from task_app.models import Task

User = get_user_model()


class BoardSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)

    class Meta:
        model = Board
        fields = ["id", "title", "owner", "members"]
        read_only_fields = ["id", "owner"]


class BoardListSerializer(serializers.ModelSerializer):
    owner_id = serializers.IntegerField(read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    ticket_count = serializers.IntegerField(read_only=True)
    tasks_to_do_count = serializers.IntegerField(read_only=True)
    tasks_high_prio_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Board
        fields = [
            "id",
            "title",
            "member_count",
            "ticket_count",
            "tasks_to_do_count",
            "tasks_high_prio_count",
            "owner_id",
        ]


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "fullname"]


class BoardTaskSerializer(serializers.ModelSerializer):
    assignee = serializers.SerializerMethodField()
    reviewer = UserSummarySerializer(read_only=True)
    due_date = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

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
            "comments_count",
        ]

    def get_assignee(self, obj):
        user = obj.assignees.order_by("id").first()
        if not user:
            return None
        return UserSummarySerializer(user).data

    def get_due_date(self, obj):
        if obj.due_date is None:
            return None
        return obj.due_date.date().isoformat()

    def get_comments_count(self, obj):
        return obj.comments.count()


class BoardDetailSerializer(serializers.ModelSerializer):
    owner_id = serializers.IntegerField(read_only=True)
    members = UserSummarySerializer(many=True, read_only=True)
    tasks = BoardTaskSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = ["id", "title", "owner_id", "members", "tasks"]


class BoardUpdateResponseSerializer(serializers.ModelSerializer):
    owner_data = UserSummarySerializer(source="owner", read_only=True)
    members_data = UserSummarySerializer(source="members", many=True, read_only=True)

    class Meta:
        model = Board
        fields = ["id", "title", "owner_data", "members_data"]


class EmailCheckQuerySerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
