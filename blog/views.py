from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from .forms import CommentForm
from .models import Book, Comment, Post

def post_list(request):
    posts = Post.objects.filter(status=Post.Status.PUBLISHED).select_related("author").prefetch_related("tags")
    page = Paginator(posts, 5).get_page(request.GET.get("page"))
    context = {"posts": page.object_list, "page": page}
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        response = render(request, "blog/_post_cards.html", context)
        response["X-Next-Page"] = page.next_page_number() if page.has_next() else ""
        return response
    return render(request, "blog/post_list.html", context)

def post_detail(request, slug):
    post = get_object_or_404(
        Post.objects.select_related("author").prefetch_related(
            "tags",
            Prefetch("comments", queryset=Comment.objects.filter(is_approved=True), to_attr="approved_comments"),
        ),
        slug=slug,
        status=Post.Status.PUBLISHED,
    )
    form = CommentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()
        messages.success(request, "Thank you. Your comment is awaiting approval.")
        return redirect(f"{post.get_absolute_url()}#komentar")
    return render(request, "blog/post_detail.html", {"post": post, "comment_form": form})


def search(request):
    query = " ".join(request.GET.get("q", "").split())[:100]
    posts = Post.objects.none()
    books = Book.objects.none()
    if query:
        posts = (
            Post.objects.filter(status=Post.Status.PUBLISHED)
            .filter(
                Q(title__icontains=query)
                | Q(excerpt__icontains=query)
                | Q(body__icontains=query)
                | Q(tags__name__icontains=query)
            )
            .select_related("author")
            .prefetch_related("tags")
            .distinct()
        )
        books = Book.objects.filter(
            Q(title__icontains=query)
            | Q(author__icontains=query)
            | Q(thoughts__icontains=query)
            | Q(lessons__icontains=query)
        )
    return render(request, "blog/search.html", {"query": query, "posts": posts, "books": books})


def library(request):
    books = Book.objects.prefetch_related("notes")
    context = {
        "stats": {
            "read": books.filter(status__in=[Book.Status.FINISHED, Book.Status.FAVORITE]).count(),
            "reading": books.filter(status=Book.Status.READING).count(),
            "want": books.filter(status=Book.Status.WANT).count(),
        },
        "reading_books": books.filter(status=Book.Status.READING),
        "favorite_books": books.filter(status=Book.Status.FAVORITE),
        "finished_books": books.filter(status=Book.Status.FINISHED),
        "want_books": books.filter(status=Book.Status.WANT),
    }
    return render(request, "blog/library.html", context)


def reading_timeline(request):
    books = list(
        Book.objects.filter(
            status__in=[Book.Status.READING, Book.Status.FINISHED, Book.Status.FAVORITE]
        )
    )
    entries = []
    for book in books:
        activity_date = book.finished_at or book.started_at
        if not activity_date:
            continue
        rating = int(book.rating or 0)
        entries.append(
            {
                "book": book,
                "date": activity_date,
                "stars": "★" * rating + "☆" * (5 - rating),
            }
        )
    entries.sort(key=lambda entry: (entry["date"], entry["book"].title), reverse=True)

    years = []
    for entry in entries:
        year_number = entry["date"].year
        month_number = entry["date"].month
        if not years or years[-1]["year"] != year_number:
            years.append({"year": year_number, "months": []})
        months = years[-1]["months"]
        if not months or months[-1]["number"] != month_number:
            months.append({"number": month_number, "date": entry["date"], "entries": []})
        months[-1]["entries"].append(entry)

    return render(request, "blog/reading_timeline.html", {"timeline_years": years})


def book_detail(request, slug):
    book = get_object_or_404(Book.objects.prefetch_related("notes"), slug=slug)
    return render(request, "blog/book_detail.html", {"book": book})
