from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import config


def home(request):
    if request.user.is_authenticated:
        return redirect('pdadns:domains')
    else:
        if config.settings.DISABLE_LANDING_PAGE:
            return redirect('account_login')
        return render(request, 'web/landing_page.html')


def send_test_email(request):
    from django.core.mail import send_mail
    from config import settings

    send_mail(
        subject='This is a test email',
        message='This is a test email.',
        from_email=settings.site_from_email,
        recipient_list=[settings.admin_email],
    )
    messages.success(request, 'Test email sent.')
    return HttpResponseRedirect(reverse('home'))


def simulate_error(request):
    raise Exception('This is a simulated error.')
