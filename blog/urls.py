from django.urls import path
from . import views

app_name = "blog"
urlpatterns = [
    path("", views.post_list, name="list"),
    path("search/", views.search, name="search"),
    path("reading/", views.reading_timeline, name="reading_timeline"),
    path("library/", views.library, name="library"),
    path("library/<slug:slug>/", views.book_detail, name="book_detail"),
    path("tulisan/<slug:slug>/", views.post_detail, name="detail"),
]
