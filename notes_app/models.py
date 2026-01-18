# notes_app/models.py
from django.db import models
import uuid
# from django.utils import timezone


class Project(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        DONE = "done", "Done"

    class Structure(models.TextChoices):
        """
        UX-режим структуры проекта:
        - topics:  Project → Topics → Sections → Entries  (4 уровня)
        - sections: Project → Sections → Entries          (3 уровня)  (через один system Topic)
        - entries: Project → Entries                      (2 уровня)  (через system Topic + system Section)
        """
        TOPICS = "topics", "Topics → Sections → Entries"
        SECTIONS = "sections", "Sections → Entries"
        ENTRIES = "entries", "Entries only"

    title = models.CharField(max_length=200)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    pinned = models.BooleanField(default=False)
    last_opened_at = models.DateTimeField(null=True, blank=True)

    # ✅ v0.1: режим структуры (по умолчанию безопаснее 3х, чтобы старые данные не “спрятались”)
    structure = models.CharField(
        max_length=20,
        choices=Structure.choices,
        default=Structure.SECTIONS,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-pinned", "-last_opened_at", "-updated_at", "-created_at")

    def __str__(self) -> str:
        return self.title


class Topic(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="topics")
    title = models.CharField(max_length=200)
    order = models.IntegerField(default=1)

    # ✅ system topic (служебный контейнер) для режимов 2х/3х
    is_system = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("order", "id")
        unique_together = [("project", "order")]

    def __str__(self) -> str:
        return f"{self.project.title} / {self.title}"


class Section(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="sections")
    title = models.CharField(max_length=200)
    order = models.IntegerField(default=1)

    # ✅ system section (служебный контейнер) для режима 2х
    is_system = models.BooleanField(default=False)

    # Указатель на текущий беловик (может быть null)
    release_snapshot = models.ForeignKey(
        "SectionSnapshot",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("order", "id")
        unique_together = [("topic", "order")]

    def __str__(self) -> str:
        return f"{self.topic.project.title} / {self.title}"



class Entry(models.Model):
    TYPE_CHOICES = [
        ("note", "Note"),
        ("prompt", "Prompt"),
        ("answer", "Answer"),
        ("artifact", "Artifact"),
        ("mixed", "Mixed"),
    ]

    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="entries")
    title = models.CharField(max_length=200, blank=True, default="")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="note")
    order = models.PositiveIntegerField(default=1)

    # ТЕКУЩИЙ ЧЕРНОВИК (перезаписываем сколько угодно раз)
    draft_delta = models.JSONField(default=dict, blank=True)   # Quill Delta
    draft_html = models.TextField(blank=True, default="")
    draft_text = models.TextField(blank=True, default="")     # plain text for search

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("order", "id")
        unique_together = [("section", "order")]

    def __str__(self) -> str:
        t = (self.title or "").strip() or "(без названия)"
        return f"Entry#{self.id} • {t}"


class EntryRevision(models.Model):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="revisions")
    rev_no = models.PositiveIntegerField(default=1)

    delta = models.JSONField(default=dict, blank=True)
    html = models.TextField(blank=True, default="")
    text = models.TextField(blank=True, default="")

    note = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(fields=["entry", "rev_no"]),
        ]

    def save(self, *args, **kwargs):
        if not self.pk:
            # авто-нумерация ревизий внутри entry
            last = EntryRevision.objects.filter(entry=self.entry).order_by("-rev_no").first()
            self.rev_no = (last.rev_no + 1) if last else 1
        super().save(*args, **kwargs)
        
    def __str__(self) -> str:
        t = (self.entry.title or "").strip() or "(без названия)"
        return f"Entry#{self.entry_id} r{self.rev_no} • {t} • {self.created_at:%Y-%m-%d %H:%M}"


class SectionSnapshot(models.Model):
    KIND_CHOICES = [
        ("snapshot", "Snapshot"),
        ("release", "Release"),
    ]

    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="snapshots")
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default="snapshot")

    rev_no = models.PositiveIntegerField(default=1)
    note = models.CharField(max_length=200, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(fields=["section", "rev_no"]),
        ]

    def save(self, *args, **kwargs):
        if not self.pk:
            last = SectionSnapshot.objects.filter(section=self.section).order_by("-rev_no").first()
            self.rev_no = (last.rev_no + 1) if last else 1
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        p = self.section.topic.project.title
        sec = self.section.title
        return f"{p} / {sec} • {self.kind} #{self.rev_no} • {self.created_at:%Y-%m-%d %H:%M}"
    
    
class SectionSnapshotItem(models.Model):
    snapshot = models.ForeignKey(SectionSnapshot, on_delete=models.CASCADE, related_name="items")
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE, related_name="+")
    entry_revision = models.ForeignKey(EntryRevision, on_delete=models.PROTECT, related_name="+")
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ("order", "id")
        unique_together = [("snapshot", "order")]
        
    def __str__(self) -> str:
        t = (self.entry.title or "").strip() or "(без названия)"
        return f"{self.snapshot.kind}#{self.snapshot.rev_no} • {t} • r{self.entry_revision.rev_no} (ord {self.order})"


def _image_upload_to(instance, filename: str) -> str:
    # всегда пишем webp, имя генерим сами
    return f"workbench/images/{instance.project_id or 'no-project'}/{uuid.uuid4().hex}.webp"


class Image(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="images",
        null=True,
        blank=True,
    )
    entry = models.ForeignKey(
        Entry,
        on_delete=models.SET_NULL,
        related_name="images",
        null=True,
        blank=True,
    )

    file = models.ImageField(upload_to=_image_upload_to)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")

    def __str__(self) -> str:
        p = f"p{self.project_id}" if self.project_id else "p?"
        e = f"e{self.entry_id}" if self.entry_id else "e?"
        return f"Image {self.id} ({p}, {e})"