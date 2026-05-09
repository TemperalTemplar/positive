"""
Management command: send_reading_reminders

Run this via cron or Docker scheduler every hour:
  python manage.py send_reading_reminders

Add to your crontab:
  0 * * * * docker exec positive_engine python manage.py send_reading_reminders
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import ReadingReminder, ReadingProgress
from core.relays import send_email_notification, send_to_discord, send_to_rocketchat
from datetime import timedelta


class Command(BaseCommand):
    help = 'Send reading reminder notifications to users'

    def handle(self, *args, **options):
        now = timezone.now()
        current_time = now.time()
        current_hour = current_time.hour
        weekday = now.weekday()  # 0=Monday, 6=Sunday

        sent = 0
        skipped = 0

        reminders = ReadingReminder.objects.filter(
            is_active=True
        ).select_related('user', 'user__profile', 'library_item')

        for reminder in reminders:
            # Check frequency
            if reminder.frequency == 'WEEKDAYS' and weekday >= 5:
                skipped += 1
                continue
            if reminder.frequency == 'WEEKLY' and weekday != 0:
                skipped += 1
                continue

            # Check if it's the right hour
            if reminder.reminder_time.hour != current_hour:
                skipped += 1
                continue

            # Check not already sent today
            if reminder.last_sent:
                hours_since = (now - reminder.last_sent).total_seconds() / 3600
                if hours_since < 20:
                    skipped += 1
                    continue

            # Get reading progress
            progress = ReadingProgress.objects.filter(
                user=reminder.user,
                item=reminder.library_item
            ).first()

            progress_text = ''
            if progress and reminder.library_item.total_pages:
                progress_text = f' (currently on page {progress.current_page} of {reminder.library_item.total_pages})'

            msg = (
                f"📖 Reading Reminder — {reminder.library_item.title}\n\n"
                f"Time for your {reminder.duration_minutes}-minute reading session{progress_text}.\n\n"
                f"— Positive"
            )

            # Send notifications
            profile = getattr(reminder.user, 'profile', None)
            notified = False

            if profile and profile.personal_email:
                send_email_notification(
                    profile.personal_email,
                    f'Reading Reminder: {reminder.library_item.title}',
                    msg
                )
                notified = True

            if profile and profile.notify_discord:
                send_to_discord(msg, title="Reading Reminder")
                notified = True

            if profile and profile.notify_rocketchat:
                send_to_rocketchat(msg)
                notified = True

            if notified:
                reminder.last_sent = now
                reminder.save()
                sent += 1
                self.stdout.write(f'  Sent reminder to {reminder.user.username} for {reminder.library_item.title}')

        self.stdout.write(self.style.SUCCESS(f'Done. Sent: {sent}, Skipped: {skipped}'))
