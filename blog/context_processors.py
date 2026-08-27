from .models import Book, SiteProfile


def site_profile(request):
    return {
        "site_profile": SiteProfile.load(),
        "currently_reading_book": Book.objects.filter(status=Book.Status.READING).first(),
    }
