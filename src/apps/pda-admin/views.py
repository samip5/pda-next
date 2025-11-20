from allauth.socialaccount.models import SocialAccount
from allauth_2fa.utils import user_has_valid_totp_device
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _


@login_required
def profile(request):
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