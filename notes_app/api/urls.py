from django.urls import path, include
from rest_framework.routers import DefaultRouter
from notes_app.api.views import (
    ProjectViewSet,
    TopicViewSet,
    SectionViewSet,
    EntryViewSet,
    SearchView,
    ImageUploadView,
)

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="projects")
router.register(r"topics", TopicViewSet, basename="topics")
router.register(r"sections", SectionViewSet, basename="sections")
router.register(r"entries", EntryViewSet, basename="entries")

urlpatterns = [
    path("", include(router.urls)),
    path("images/upload/", ImageUploadView.as_view()),
    path("search/", SearchView.as_view(), name="search"),
]
