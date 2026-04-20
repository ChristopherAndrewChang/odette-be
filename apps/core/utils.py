from datetime import datetime, timedelta
from django.utils import timezone


def get_session_day_type():
    now = timezone.localtime(timezone.now())
    if now.hour < 12:
        session_date = (now - timedelta(days=1)).date()
    else:
        session_date = now.date()
    return 'weekend' if session_date.weekday() >= 4 else 'weekday'


def get_session_date(dt):
    local = timezone.localtime(dt)
    if local.hour < 12:
        return (local - timedelta(days=1)).date()
    return local.date()


def get_session_range(session_date):
    tz = timezone.get_current_timezone()
    start = datetime(session_date.year, session_date.month, session_date.day, 20, 0, tzinfo=tz)
    end = start + timedelta(hours=8)
    return start, end