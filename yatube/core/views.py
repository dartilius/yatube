from django.shortcuts import render


def page_not_found(request, exception):
    """Кастомная страница 404."""
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def permission_denied(request, exception):
    """Страница отказано в доступе."""
    return render(request, 'core/403.html', status=403)


def csrf_failure(request, reason=''):
    """Кастомная страница 403."""
    return render(request, 'core/403csrf.html')


def server_error(request):
    """Кастомная страница 500."""
    return render(
        request,
        'core/500.html',
        status=500
    )
