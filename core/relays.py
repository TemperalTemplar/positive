import os
import requests
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import send_mail


def send_to_discord(content, title="Positive Update", color=52224, link=None):
    webhook = getattr(settings, 'DISCORD_WEBHOOK', '')
    if not webhook:
        return False
    payload = {
        "embeds": [{
            "title": title,
            "description": content,
            "url": link or "",
            "color": color,
            "footer": {"text": "Sovereign Intent Engine | Positive"},
            "timestamp": datetime.utcnow().isoformat()
        }]
    }
    try:
        r = requests.post(webhook, json=payload, timeout=5)
        return r.status_code == 204
    except Exception:
        return False


def send_to_rocketchat(message, link=None):
    webhook = getattr(settings, 'ROCKETCHAT_WEBHOOK', '')
    if not webhook:
        return False
    payload = {
        "text": message,
        "attachments": [{"title": "View in Positive", "title_link": link, "color": "#00d4a0"}] if link else []
    }
    try:
        r = requests.post(webhook, json=payload, timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def send_email_notification(to_email, subject, body):
    if not to_email:
        return False
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [to_email])
        return True
    except Exception:
        return False


def create_ics_event(title, duration_minutes, description=""):
    try:
        from icalendar import Calendar, Event
        cal = Calendar()
        event = Event()
        now = datetime.utcnow()
        event.add('summary', f"Positive: {title}")
        event.add('dtstart', now)
        event.add('dtend', now + timedelta(minutes=duration_minutes))
        event.add('description', description or f"Intent session: {title}")
        cal.add_component(event)
        fname = f"{title.lower().replace(' ', '_')}_{now.strftime('%Y%m%d%H%M')}.ics"
        fpath = os.path.join(settings.MEDIA_ROOT, 'calendar_events', fname)
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        with open(fpath, 'wb') as f:
            f.write(cal.to_ical())
        return fpath, fname
    except Exception:
        return None, None


def dispatch_timer_complete(timer):
    user = timer.user
    profile = getattr(user, 'profile', None)
    msg = f"Session complete: {timer.title} ({timer.duration_minutes} min)"
    if timer.create_calendar_event:
        create_ics_event(timer.title, timer.duration_minutes)
    if timer.send_to_email and profile and profile.personal_email:
        send_email_notification(profile.personal_email, f"Positive: {timer.title} complete", msg)
    if timer.send_to_discord:
        send_to_discord(msg, title="Session Complete")
    if timer.send_to_rocketchat:
        send_to_rocketchat(msg)


def dispatch_entry_created(entry):
    if entry.is_private:
        return
    msg = f"New {entry.get_category_display()} from {entry.user.username}:\n\n{entry.content[:200]}"
    send_to_discord(msg, title=f"New {entry.get_category_display()}")
    send_to_rocketchat(msg)


def dispatch_vision_board_published(board, url):
    msg = f"{board.owner.username} published Vision Board: {board.name}"
    send_to_discord(msg, title="Vision Board Published", link=url)
    send_to_rocketchat(msg, link=url)
