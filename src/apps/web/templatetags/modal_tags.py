"""
Reusable Alpine.js + HTMX modal component for Django templates.

Usage:

    {% load modal_tags %}

    {% modal id="create-record" title="Create Record" size="md" %}

        {% modaltrigger %}
            <button @click="open = true" class="btn btn-primary mb-4">
                <i class="fa fa-plus"></i>
            </button>
        {% endmodaltrigger %}

        <!-- anything here (not wrapped in modaltrigger/modalfooter) is the body -->
        <form method="post" hx-post="{% url 'record_create' %}">
            {% csrf_token %}
            ...
        </form>

        {% modalfooter %}
            <button @click="open = false" class="btn btn-secondary">Close</button>
        {% endmodalfooter %}

    {% endmodal %}

If you omit {% modaltrigger %} or {% modalfooter %}, sensible defaults are
used, so both are optional and independently overridable per-instance.
"""

from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

register = template.Library()

SIZE_CLASSES = {
    "sm": "max-w-sm",
    "md": "max-w-md",
    "lg": "max-w-lg",
    "xl": "max-w-xl",
    "full": "max-w-full",
}

DEFAULT_TRIGGER = """
<button @click="open = true" class="btn btn-primary">Open</button>
"""

DEFAULT_FOOTER = """
<button @click="open = false" class="btn btn-secondary">Close</button>
"""


class ModalTriggerNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        return self.nodelist.render(context)


class ModalFooterNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        return self.nodelist.render(context)


@register.tag(name="modaltrigger")
def do_modaltrigger(parser, token):
    nodelist = parser.parse(("endmodaltrigger",))
    parser.delete_first_token()
    return ModalTriggerNode(nodelist)


@register.tag(name="modalfooter")
def do_modalfooter(parser, token):
    nodelist = parser.parse(("endmodalfooter",))
    parser.delete_first_token()
    return ModalFooterNode(nodelist)


class ModalNode(template.Node):
    def __init__(self, nodelist, kwargs):
        self.nodelist = nodelist
        self.kwargs = kwargs  # dict[str, FilterExpression]

    def render(self, context):
        trigger_html = ""
        footer_html = ""
        body_parts = []

        # Walk the top-level nodes: pull out trigger/footer, everything
        # else becomes the modal body, in document order.
        for node in self.nodelist:
            if isinstance(node, ModalTriggerNode):
                trigger_html += node.render(context)
            elif isinstance(node, ModalFooterNode):
                footer_html += node.render(context)
            else:
                body_parts.append(node.render(context))

        resolved = {key: val.resolve(context) for key, val in self.kwargs.items()}

        modal_id = resolved.get("id") or "modal"
        title = resolved.get("title", "")
        size = resolved.get("size", "md")
        size_class = SIZE_CLASSES.get(size, SIZE_CLASSES["md"])

        return render_to_string(
            "web/components/modal.html",
            {
                "modal_id": modal_id,
                "title": title,
                "size_class": size_class,
                "trigger_html": mark_safe(trigger_html or DEFAULT_TRIGGER),
                "body_html": mark_safe("".join(body_parts)),
                "footer_html": mark_safe(footer_html or DEFAULT_FOOTER),
            },
        )


@register.tag(name="modal")
def do_modal(parser, token):
    bits = token.split_contents()[1:]
    kwargs = {}
    for bit in bits:
        if "=" not in bit:
            raise template.TemplateSyntaxError(
                f"'modal' tag arguments must be key=value pairs, got '{bit}'"
            )
        key, value = bit.split("=", 1)
        kwargs[key] = parser.compile_filter(value)

    nodelist = parser.parse(("endmodal",))
    parser.delete_first_token()
    return ModalNode(nodelist, kwargs)