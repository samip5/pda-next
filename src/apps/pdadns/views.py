
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

"""
Frontend Views
"""

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

@login_required
def domain(request, id):
    return render(
        request,
        "dns/domain.html",
        {
            "active_tab": "domain",
            "page_title": _("Domain"),
            "id": id,
            "rrsets":[
                {"name":"@", "type":"A", "status":"Active", "ttl":"3600", "data":"91.232.155.81" },
                {"name": "@", "type": "MX", "status": "Active", "ttl": "3600", "data": "mx2.kapsi.fi."},
                {"name": "@", "type": "AAAA", "status": "Active", "ttl": "3600", "data": "2001:67c:1be8:1337::443"}
            ]
        },
    )