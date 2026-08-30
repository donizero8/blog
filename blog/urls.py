from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = "blog"
urlpatterns = [
    path("", views.post_list, name="list"),
    path("search/", views.search, name="search"),
    path("reading/", views.reading_timeline, name="reading_timeline"),
    path("library/", views.library, name="library"),
    path("library/<slug:slug>/", views.book_detail, name="book_detail"),
    path("posts/<slug:slug>/", views.post_detail, name="detail"),
    path(
        "tulisan/<slug:slug>/",
        RedirectView.as_view(pattern_name="blog:detail", permanent=True),
        name="legacy_detail",
    ),
]
