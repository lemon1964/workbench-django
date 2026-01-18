from rest_framework import serializers
from notes_app.models import Project, Topic, Section, Entry
from ..services import ensure_project_entrypoint


class ProjectSerializer(serializers.ModelSerializer):
    entrypoint_section_id = serializers.IntegerField(read_only=True)
    entrypoint_entry_id = serializers.IntegerField(read_only=True)
    class Meta:
        model = Project
        fields = ("id", "title", "status", "structure", "pinned", "last_opened_at",
                  "created_at", "updated_at",
                  "entrypoint_section_id", "entrypoint_entry_id")
        # fields = ["id", "title", "status", "pinned", "last_opened_at", "created_at", "updated_at"]

    def create(self, validated_data):
        project = super().create(validated_data)
        section, entry = ensure_project_entrypoint(project)

        # просто добавляем “виртуальные” поля в инстанс для ответа
        project.entrypoint_section_id = section.id
        project.entrypoint_entry_id = entry.id
        return project

class SectionMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ["id", "title", "order"]


class TopicTreeSerializer(serializers.ModelSerializer):
    sections = SectionMiniSerializer(many=True, read_only=True)

    class Meta:
        model = Topic
        fields = ["id", "title", "order", "sections"]


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ("id", "project", "title", "order", "is_system")  # ✅ v0.1
        # fields = ["id", "project", "title", "order", "created_at"]


class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ("id", "topic", "title", "order", "is_system")  # ✅ v0.1
        # fields = ["id", "topic", "title", "order", "release_snapshot", "created_at"]


class EntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entry
        fields = [
            "id", "section", "title", "type", "order",
            "draft_delta", "draft_html", "draft_text",
            "updated_at"
        ]


class EntryDraftUpdateSerializer(serializers.ModelSerializer):
    """Обычное 'рабочее сохранение' (перезапись текущего draft)"""
    class Meta:
        model = Entry
        fields = ["draft_delta", "draft_html", "draft_text", "title", "type"]
        extra_kwargs = {
            "draft_delta": {"required": False},
            "draft_html": {"required": False},
            "draft_text": {"required": False},
            "title": {"required": False},
            "type": {"required": False},
        }


class SnapshotRequestSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True)
    entry_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
