from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("manual-events", views.ManualEventViewSet, basename="manual-event")

urlpatterns = [
    path("events/", views.EventListView.as_view(), name="event-list"),
    path("events/saved/", views.SavedEventListView.as_view(), name="event-saved-list"),
    path("events/<int:pk>/save/", views.EventSaveView.as_view(), name="event-save"),
    path("events/<int:pk>/hide/", views.EventHideView.as_view(), name="event-hide"),
] + router.urls
