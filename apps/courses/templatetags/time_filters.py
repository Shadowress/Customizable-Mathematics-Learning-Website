from django import template

register = template.Library()


@register.filter
def time_format(seconds):
    try:
        seconds = int(float(seconds))
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours}:{minutes:02}:{secs:02}"
        return f"{minutes}:{secs:02}"
    except (ValueError, TypeError):
        return "0:00"
