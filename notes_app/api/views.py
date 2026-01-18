# notes_app/api/views.py
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from notes_app.models import Project, Topic, Section, Entry, SectionSnapshotItem, Image
from notes_app.api.serializers import (
    ProjectSerializer,
    TopicSerializer,
    SectionSerializer,
    EntrySerializer,
    EntryDraftUpdateSerializer,
    TopicTreeSerializer,
    SnapshotRequestSerializer,
)
from notes_app.services import snapshot_section, make_release, ensure_project_entrypoint
from rest_framework.parsers import MultiPartParser, FormParser
from PIL import Image as PILImage
from io import BytesIO
from django.core.files.base import ContentFile
import uuid


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    @action(detail=True, methods=["get"])
    def tree(self, request, pk=None):
        project = self.get_object()

        # ✅ v0.2: самоисцеление (гарантирует точку входа)
        ensure_project_entrypoint(project)

        topics = (
            Topic.objects
            .filter(project=project)
            .prefetch_related("sections")
            .order_by("order", "id")
        )
        data = TopicTreeSerializer(topics, many=True).data
        return Response({"project": ProjectSerializer(project).data, "topics": data})


class TopicViewSet(viewsets.ModelViewSet):
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        project_id = self.request.query_params.get("project")
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs.order_by("order", "id")


class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        topic_id = self.request.query_params.get("topic")
        if topic_id:
            qs = qs.filter(topic_id=topic_id)
        return qs.order_by("order", "id")

    @action(detail=True, methods=["get"])
    def entries(self, request, pk=None):
        section = self.get_object()
        qs = Entry.objects.filter(section=section).order_by("order", "id")
        return Response(EntrySerializer(qs, many=True).data)

    @action(detail=True, methods=["post"])
    def snapshot(self, request, pk=None):
        section = self.get_object()
        ser = SnapshotRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        note = ser.validated_data.get("note", "")
        entry_ids = ser.validated_data.get("entry_ids", None)

        snap = snapshot_section(section=section, kind="snapshot", note=note, entry_ids=entry_ids)
        return Response({"snapshot_id": snap.id, "rev_no": snap.rev_no}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def release(self, request, pk=None):
        section = self.get_object()
        note = (request.data or {}).get("note", "")
        snap = make_release(section=section, note=note)
        return Response({"release_snapshot_id": snap.id, "rev_no": snap.rev_no}, status=status.HTTP_201_CREATED)


class EntryViewSet(viewsets.ModelViewSet):
    queryset = Entry.objects.all()
    serializer_class = EntrySerializer

    def get_queryset(self):
        qs = super().get_queryset()
        section_id = self.request.query_params.get("section")
        if section_id:
            qs = qs.filter(section_id=section_id)
        return qs.order_by("order", "id")

    @action(detail=True, methods=["patch"])
    def draft(self, request, pk=None):
        entry = self.get_object()
        ser = EntryDraftUpdateSerializer(entry, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(EntrySerializer(entry).data)


class SearchView(APIView):
    """
    GET /api/search/?q=...&scope=global|project&project_id=...&only=draft|release|all
    """
    def get(self, request):
        q = (request.query_params.get("q") or "").strip()
        scope = request.query_params.get("scope", "global")
        project_id = request.query_params.get("project_id")
        only = request.query_params.get("only", "draft")  # draft|release|all

        if not q:
            return Response({"results": []})

        results = []

        # --- draft search (Entry.draft_text) ---
        if only in ("draft", "all"):
            entries = Entry.objects.select_related("section__topic__project").filter(
                draft_text__icontains=q
            )
            if scope == "project" and project_id:
                entries = entries.filter(section__topic__project_id=project_id)

            for e in entries[:50]:
                results.append({
                    "kind": "draft",
                    "project_id": e.section.topic.project_id,
                    "project_title": e.section.topic.project.title,
                    "topic_id": e.section.topic_id,
                    "topic_title": e.section.topic.title,
                    "section_id": e.section_id,
                    "section_title": e.section.title,
                    "entry_id": e.id,
                    "entry_title": e.title,
                })

        # --- release search (по ревизиям беловиков) ---
        if only in ("release", "all"):
            items = SectionSnapshotItem.objects.select_related(
                "snapshot__section__topic__project",
                "entry",
                "entry_revision",
            ).filter(
                snapshot__kind="release",
                entry_revision__text__icontains=q
            )
            if scope == "project" and project_id:
                items = items.filter(snapshot__section__topic__project_id=project_id)

            for it in items[:50]:
                sec = it.snapshot.section
                results.append({
                    "kind": "release",
                    "project_id": sec.topic.project_id,
                    "project_title": sec.topic.project.title,
                    "topic_id": sec.topic_id,
                    "topic_title": sec.topic.title,
                    "section_id": sec.id,
                    "section_title": sec.title,
                    "entry_id": it.entry_id,
                    "entry_title": it.entry.title,
                    "snapshot_id": it.snapshot_id,
                    "entry_revision_id": it.entry_revision_id,
                })

        return Response({"results": results})
    

class ImageUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    # MVP лимиты/нормализация
    MAX_UPLOAD_BYTES = 10 * 1024 * 1024   # 10MB входной файл
    MAX_SIDE = 2000                       # max ширина/высота после ресайза
    WEBP_QUALITY = 85

    def post(self, request):
        f = request.FILES.get("file")
        if not f:
            return Response({"detail": "file is required"}, status=400)

        content_type = getattr(f, "content_type", "") or ""
        if not content_type.startswith("image/"):
            return Response({"detail": "only image/* allowed"}, status=400)

        if f.size and f.size > self.MAX_UPLOAD_BYTES:
            return Response({"detail": "file too large"}, status=400)

        # привязки (мы хотим project+entry)
        entry = None
        project = None

        entry_id = request.data.get("entry_id")
        project_id = request.data.get("project_id")

        if entry_id:
            entry = Entry.objects.select_related("section__topic__project").get(pk=int(entry_id))
            project = entry.section.topic.project
        elif project_id:
            project = Project.objects.get(pk=int(project_id))

        # Pillow: открыть, ресайз, webp
        try:
            img = PILImage.open(f)
            img.load()

            # нормализуем цветовой режим
            if img.mode in ("P", "LA"):
                img = img.convert("RGBA")
            elif img.mode == "CMYK":
                img = img.convert("RGB")

            # ресайз (без апскейла)
            img.thumbnail((self.MAX_SIDE, self.MAX_SIDE))

            out = BytesIO()
            # webp поддерживает alpha (RGBA) — ок
            img.save(out, format="WEBP", quality=self.WEBP_QUALITY, method=6)
            out.seek(0)

            wb = Image(project=project, entry=entry)
            wb.width, wb.height = img.size

            filename = f"{uuid.uuid4().hex}.webp"
            wb.file.save(filename, ContentFile(out.getvalue()), save=True)

            return Response(
                {"id": wb.id, "url": wb.file.url, "width": wb.width, "height": wb.height},
                status=201,
            )

        except Exception as e:
            return Response({"detail": f"image processing failed: {str(e)}"}, status=400)

