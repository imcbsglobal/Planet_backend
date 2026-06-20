from django.urls import path
from .views import FeederListCreateView, FeederDetailView

urlpatterns = [
    path("feeders/",      FeederListCreateView.as_view(), name="feeder-list-create"),
    path("feeders/<int:pk>/", FeederDetailView.as_view(),    name="feeder-detail"),
]