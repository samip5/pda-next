from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _


@login_required
def domains(request):
    return render(
        request,
        "dns/domains.html",
        {
            "active_tab": "domains",
            "page_title": _("Domains"),
            "zones":[{"domain":"cappe.fi", "type":"Native", "primary":"N/A", "account":"None", "serial":"2025112001" }]
        },
    )
