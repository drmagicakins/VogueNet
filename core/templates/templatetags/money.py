# core/templatetags/money.py
from django import template
register = template.Library()

@register.filter
def naira_from_kobo(val):
    try:
        return f"{(int(val)/100):,.2f}"
    except Exception:
        return val
