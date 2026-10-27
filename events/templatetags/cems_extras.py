from django import template
from django.utils import timezone
from datetime import date, datetime
from decimal import Decimal

register = template.Library()


@register.filter(name="inr")
def inr(value):
    """
    Format currency as 'Free' for 0 or '₹150' (strips .00 if whole number).
    """
    if value is None:
        return "Free"
    try:
        val = Decimal(str(value))
        if val <= 0:
            return "Free"
        if val % 1 == 0:
            return f"₹{int(val)}"
        return f"₹{val:.2f}"
    except (ValueError, TypeError):
        return "Free"


@register.filter(name="short_date")
def short_date(value):
    """
    Format date as '14 Nov 2026' (no leading zero on day).
    """
    if not value:
        return ""
    if isinstance(value, datetime):
        value = timezone.localdate(value) if timezone.is_aware(value) else value.date()
    if isinstance(value, date):
        return f"{value.day} {value.strftime('%b %Y')}"
    return str(value)


@register.filter(name="day_num")
def day_num(value):
    if not value:
        return ""
    if isinstance(value, (datetime, date)):
        return str(value.day)
    return ""


@register.filter(name="month_abbr")
def month_abbr(value):
    if not value:
        return ""
    if isinstance(value, (datetime, date)):
        return value.strftime("%b").upper()
    return ""


@register.filter(name="time_12h")
def time_12h(value):
    """
    Format time as '7:49 PM' (no leading zero on hour).
    """
    if not value:
        return ""
    if isinstance(value, datetime):
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        hour = value.strftime("%I").lstrip("0") or "12"
        minute = value.strftime("%M")
        ampm = value.strftime("%p")
        return f"{hour}:{minute} {ampm}"
    return ""


@register.filter(name="datetime_full")
def datetime_full(value):
    """
    Format as '27 Oct 2026, 7:49 PM'.
    """
    if not value:
        return ""
    if isinstance(value, datetime):
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        d = f"{value.day} {value.strftime('%b %Y')}"
        t = time_12h(value)
        return f"{d}, {t}"
    return short_date(value)


@register.filter(name="relative_day")
def relative_day(value):
    """
    Relative day hint: 'Past', 'Today', 'Tomorrow', 'In X days'.
    """
    if not value:
        return ""
    if isinstance(value, datetime):
        target_date = timezone.localdate(value) if timezone.is_aware(value) else value.date()
    elif isinstance(value, date):
        target_date = value
    else:
        return ""

    today = timezone.localdate()
    delta = (target_date - today).days

    if delta < 0:
        return "Past"
    elif delta == 0:
        return "Today"
    elif delta == 1:
        return "Tomorrow"
    elif delta < 30:
        return f"In {delta} days"
    else:
        months = delta // 30
        return f"In {months} mo" if months > 1 else "In 1 mo"


@register.filter(name="initials")
def initials(value):
    """
    Return 2-letter uppercase initials from full name or username.
    """
    if not value:
        return "U"
    # If user object passed
    if hasattr(value, "full_name") or hasattr(value, "username"):
        name = getattr(value, "full_name", "") or getattr(value, "username", "")
    else:
        name = str(value)

    parts = name.strip().split()
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[-1][0]}".upper()
    elif parts and len(parts[0]) >= 2:
        return parts[0][:2].upper()
    elif parts:
        return parts[0][0].upper()
    return "U"


@register.filter(name="category_dot_color")
def category_dot_color(category):
    """
    Muted desaturated dot colors for categories:
    Technical: blue-slate (#475569)
    Cultural: plum (#7e22ce)
    Sports: green (#15803d)
    Workshop: amber (#b45309)
    Seminar: teal (#0f766e)
    """
    cat = str(category or "").strip().lower()
    if "tech" in cat:
        return "#475569"
    elif "cult" in cat:
        return "#7e22ce"
    elif "sport" in cat:
        return "#15803d"
    elif "work" in cat:
        return "#b45309"
    elif "sem" in cat:
        return "#0f766e"
    return "#64748b"

