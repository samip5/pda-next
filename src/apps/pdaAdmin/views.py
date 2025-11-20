from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _


@login_required
def dashboard(request):
    return render(
        request,
        "admin/test.html",
        {
            "active_tab": "admin_dash",
            "page_title": _("Admin"),
        },
    )

@login_required
def settings(request):
    return render(
        request,
        "admin/settings.html",
        {
            "active_tab": "admin_settings",
            "page_title": _("Settings"),
        },
    )