from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    ROLE_CHOICES = [('ARCHITECT', 'Architect'), ('PRACTITIONER', 'Practitioner'), ('GUEST', 'Guest')]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='PRACTITIONER')
    personal_email = models.EmailField(blank=True)
    discord_id = models.CharField(max_length=255, blank=True)
    rocketchat_id = models.CharField(max_length=255, blank=True)
    notify_email = models.BooleanField(default=True)
    notify_discord = models.BooleanField(default=False)
    notify_rocketchat = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Entry(models.Model):
    CATEGORY_CHOICES = [
        ('THOUGHT', 'Good Thought'),
        ('PRAYER', 'Prayer'),
        ('GRATITUDE', 'Gratitude'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='entries')
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    content = models.TextField()
    is_private = models.BooleanField(default=True)
    is_answered = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.category}] {self.user.username}"


class LibraryItem(models.Model):
    MEDIA_TYPES = [
        ('AUDIO', 'Audio'),
        ('VIDEO', 'Video'),
        ('TEXT', 'Text'),
    ]
    ACCESS_LEVELS = [('GLOBAL', 'Global'), ('PRIVATE', 'Private')]
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='library_items')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    media_type = models.CharField(max_length=5, choices=MEDIA_TYPES)
    access_level = models.CharField(max_length=10, choices=ACCESS_LEVELS, default='PRIVATE')
    file = models.FileField(upload_to='library/')
    total_pages = models.IntegerField(blank=True, null=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-added_at']

    def __str__(self):
        return f"[{self.media_type}] {self.title}"


class ReadingProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(LibraryItem, on_delete=models.CASCADE)
    current_page = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    last_read = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'item')

    @property
    def progress_pct(self):
        if self.item.total_pages and self.item.total_pages > 0:
            return int((self.current_page / self.item.total_pages) * 100)
        return 0


class IntentTimer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='timers')
    title = models.CharField(max_length=100)
    duration_minutes = models.IntegerField()
    library_item = models.ForeignKey(LibraryItem, null=True, blank=True, on_delete=models.SET_NULL)
    send_to_email = models.BooleanField(default=True)
    send_to_discord = models.BooleanField(default=False)
    send_to_rocketchat = models.BooleanField(default=False)
    create_calendar_event = models.BooleanField(default=True)
    is_active = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.title}"


class VisionBoard(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vision_boards')
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    is_public = models.BooleanField(default=False)
    html_file = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.owner.username}: {self.name}"


class VisionBoardImage(models.Model):
    board = models.ForeignKey(VisionBoard, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='uploads/')
    caption = models.CharField(max_length=255, blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']


class RegistrationRequest(models.Model):
    STATUS_CHOICES = [('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('DENIED', 'Denied')]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='registration_request')
    note = models.TextField(blank=True, help_text="Why do you want to join?")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_requests')

    def __str__(self):
        return f"{self.user.username} — {self.status}"
