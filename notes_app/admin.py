# notes_app/admin.py
from django.contrib import admin
from django.db.models import Exists, OuterRef
from .models import (
    Project, Topic, Section, Entry,
    EntryRevision, SectionSnapshot, SectionSnapshotItem
)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "structure", "pinned", "last_opened_at", "updated_at")
    list_filter = ("status", "structure", "pinned")
    search_fields = ("title",)
    ordering = ("-pinned", "-last_opened_at", "-updated_at", "-created_at")


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "order", "title", "is_system", "created_at")
    list_filter = ("is_system", "project")
    search_fields = ("title", "project__title")
    list_select_related = ("project",)


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("id", "project_title", "topic", "order", "title", "is_system", "release_snapshot", "created_at")
    list_filter = ("is_system", "topic__project")
    search_fields = ("title", "topic__title", "topic__project__title")
    list_select_related = ("topic", "topic__project", "release_snapshot")

    @admin.display(description="Project")
    def project_title(self, obj):
        return obj.topic.project.title

    # ✅ важное: показывать в выборе release_snapshot только kind="release"
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "release_snapshot":
            kwargs["queryset"] = SectionSnapshot.objects.filter(kind="release")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ("id", "section", "order", "type", "title", "updated_at")
    list_filter = ("type", "section__topic__project")
    search_fields = ("title", "section__title", "section__topic__project__title")
    list_select_related = ("section", "section__topic", "section__topic__project")


@admin.register(EntryRevision)
class EntryRevisionAdmin(admin.ModelAdmin):
    list_display = ("id", "entry", "rev_no", "created_at", "note")
    list_filter = ("entry__section__topic__project",)
    search_fields = ("entry__title", "note")
    list_select_related = ("entry", "entry__section", "entry__section__topic", "entry__section__topic__project")
    ordering = ("-created_at", "-id")


@admin.register(SectionSnapshot)
class SectionSnapshotAdmin(admin.ModelAdmin):
    list_display = ("id", "project_title", "section", "kind", "rev_no", "created_at", "note")
    list_filter = ("kind", "section__topic__project")
    search_fields = ("section__title", "note", "section__topic__project__title")
    list_select_related = ("section", "section__topic", "section__topic__project")
    ordering = ("-created_at", "-id")

    @admin.display(description="Project")
    def project_title(self, obj):
        return obj.section.topic.project.title


@admin.register(SectionSnapshotItem)
class SectionSnapshotItemAdmin(admin.ModelAdmin):
    list_display = ("id", "snapshot", "entry", "entry_revision", "order")
    list_filter = ("snapshot__kind", "snapshot__section__topic__project")
    search_fields = ("entry__title", "snapshot__note")
    list_select_related = ("snapshot", "snapshot__section", "snapshot__section__topic", "snapshot__section__topic__project",
                           "entry", "entry_revision")
    ordering = ("snapshot", "order", "id")

# # notes_app/admin.py
# from django.contrib import admin

# from notes_app.models import (
#     Project,
#     Topic,
#     Section,
#     Entry,
#     EntryRevision,
#     SectionSnapshot,
#     SectionSnapshotItem,
# )


# @admin.register(Project)
# class ProjectAdmin(admin.ModelAdmin):
#     """Проект (аналог курса/пространства работы)."""
#     list_display = ("id", "title", "status", "pinned", "last_opened_at", "updated_at")
#     list_filter = ("status", "pinned")
#     search_fields = ("title",)
#     ordering = ("-updated_at",)


# @admin.register(Topic)
# class TopicAdmin(admin.ModelAdmin):
#     """Тема внутри проекта (аналог модуля)."""
#     list_display = ("id", "title", "project", "order", "created_at")
#     list_filter = ("project",)
#     search_fields = ("title", "project__title")
#     ordering = ("project", "order", "id")


# @admin.register(Section)
# class SectionAdmin(admin.ModelAdmin):
#     """Раздел/кластер (аналог урока)."""
#     list_display = ("id", "title", "topic", "order", "release_snapshot", "created_at")
#     list_filter = ("topic__project", "topic")
#     search_fields = ("title", "topic__title", "topic__project__title")
#     ordering = ("topic", "order", "id")


# @admin.register(Entry)
# class EntryAdmin(admin.ModelAdmin):
#     """Запись/шаг (атом контента)."""
#     list_display = ("id", "title", "type", "section", "order", "updated_at")
#     list_filter = ("type", "section__topic__project")
#     search_fields = ("title", "draft_text", "section__title", "section__topic__title")
#     ordering = ("section", "order", "id")


# @admin.register(EntryRevision)
# class EntryRevisionAdmin(admin.ModelAdmin):
#     """Ревизия записи (беловик/снимок)."""
#     list_display = ("id", "entry", "created_at", "note")
#     list_filter = ("entry__section__topic__project",)
#     search_fields = ("entry__title", "text", "note")
#     ordering = ("-created_at",)


# @admin.register(SectionSnapshot)
# class SectionSnapshotAdmin(admin.ModelAdmin):
#     """Снимок секции: draft snapshot / release."""
#     list_display = ("id", "section", "kind", "rev_no", "created_at", "note")
#     list_filter = ("kind", "section__topic__project")
#     search_fields = ("section__title", "note")
#     ordering = ("-created_at",)


# @admin.register(SectionSnapshotItem)
# class SectionSnapshotItemAdmin(admin.ModelAdmin):
#     """Состав снимка: какие EntryRevision вошли в SectionSnapshot."""
#     list_display = ("id", "snapshot", "entry", "entry_revision")
#     list_filter = ("snapshot__kind", "snapshot__section__topic__project")
#     search_fields = ("entry__title",)
#     ordering = ("-id",)
