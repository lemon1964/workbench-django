# notes_app/services.py
from typing import Iterable, Optional
from django.db import transaction

from .models import Project, Topic, Section, Entry, EntryRevision, SectionSnapshot, SectionSnapshotItem

@transaction.atomic
def snapshot_section(section: Section, kind: str = "snapshot", note: str = "", entry_ids: Optional[Iterable[int]] = None) -> SectionSnapshot:
# def snapshot_section(section: Section, kind: str = "snapshot", note: str = "", entry_ids: Iterable[int] | None = None) -> SectionSnapshot:
    """
    Создаёт SectionSnapshot из текущих draft entries.
    Можно снимок всего раздела или только выбранных entry_ids.
    """
    qs = Entry.objects.filter(section=section).order_by("order", "id")
    if entry_ids is not None:
        qs = qs.filter(id__in=list(entry_ids))

    snapshot = SectionSnapshot.objects.create(section=section, kind=kind, note=note)

    items = []
    order = 1
    for entry in qs:
        rev = EntryRevision.objects.create(
            entry=entry,
            delta=entry.draft_delta,
            html=entry.draft_html,
            text=entry.draft_text,
            note="",
        )
        items.append(SectionSnapshotItem(
            snapshot=snapshot,
            entry=entry,
            entry_revision=rev,
            order=order,
        ))
        order += 1

    SectionSnapshotItem.objects.bulk_create(items)
    return snapshot


@transaction.atomic
def make_release(section: Section, note: str = "") -> SectionSnapshot:
    snap = snapshot_section(section=section, kind="release", note=note, entry_ids=None)
    section.release_snapshot = snap
    section.save(update_fields=["release_snapshot"])
    return snap


def _empty_delta():
    return {"ops": [{"insert": "\n"}]}

@transaction.atomic
def ensure_project_entrypoint(project: Project) -> tuple[Section, Entry]:
    # 1) Если уже есть хоть одна секция в проекте — используем её (ничего не ломаем)
    first_section = (
        Section.objects
        .select_related("topic")
        .filter(topic__project=project)
        .order_by("topic__order", "topic__id", "order", "id")
        .first()
    )
    if first_section:
        section = first_section
    else:
        # 2) Секции нет — берём первый topic или создаём новый
        first_topic = (
            Topic.objects
            .filter(project=project)
            .order_by("order", "id")
            .first()
        )

        if not first_topic:
            if project.structure == Project.Structure.TOPICS:
                topic_title = "Тема 1"
                is_system_topic = False
            else:
                topic_title = "📌 system"
                is_system_topic = True

            first_topic = Topic.objects.create(
                project=project,
                title=topic_title,
                order=1,
                is_system=is_system_topic,
            )

        # 3) Создаём первую секцию в найденном/созданном topic
        if project.structure == Project.Structure.ENTRIES:
            section_title = "📌 Входящие"
            is_system_section = True
        else:
            section_title = "Раздел 1"
            is_system_section = False

        section = Section.objects.create(
            topic=first_topic,
            title=section_title,
            order=1,
            is_system=is_system_section,
        )

    # 4) Гарантируем первую запись
    entry = Entry.objects.filter(section=section).order_by("order", "id").first()
    if not entry:
        entry = Entry.objects.create(
            section=section,
            title="Первая запись",
            type="note",
            order=1,
            draft_delta=_empty_delta(),
            draft_text="",
            draft_html="<p></p>",
        )

    return section, entry

