from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils.text import slugify
from django.db.models import Q
from .models import Entry, LibraryItem, IntentTimer, VisionBoard, VisionBoardImage, UserProfile, ReadingProgress
from .relays import dispatch_entry_created, dispatch_timer_complete, dispatch_vision_board_published
from .vision_generator import generate_vision_board_html


@login_required
def dashboard(request):
    user = request.user
    entries = Entry.objects.filter(
        Q(user=user) | Q(is_private=False)
    ).order_by('-created_at')[:30]

    audio_items = LibraryItem.objects.filter(
        media_type='AUDIO'
    ).filter(Q(owner=user) | Q(access_level='GLOBAL'))

    video_items = LibraryItem.objects.filter(
        media_type='VIDEO'
    ).filter(Q(owner=user) | Q(access_level='GLOBAL'))

    text_items = LibraryItem.objects.filter(
        media_type='TEXT'
    ).filter(Q(owner=user) | Q(access_level='GLOBAL'))

    timers = IntentTimer.objects.filter(user=user, completed=False)
    boards = VisionBoard.objects.filter(owner=user)
    reading = ReadingProgress.objects.filter(user=user, is_active=True).select_related('item')

    stats = {
        'thoughts': Entry.objects.filter(user=user, category='THOUGHT').count(),
        'prayers_active': Entry.objects.filter(user=user, category='PRAYER', is_answered=False).count(),
        'prayers_answered': Entry.objects.filter(user=user, category='PRAYER', is_answered=True).count(),
        'gratitude': Entry.objects.filter(user=user, category='GRATITUDE').count(),
    }

    # Group activity
    from django.utils import timezone as tz
    import django.db.models as dm
    now = tz.now()
    dismissed_ids = BroadcastDismissal.objects.filter(user=user).values_list('broadcast_id', flat=True)
    broadcasts = BroadcastMessage.objects.filter(
        is_active=True
    ).exclude(id__in=dismissed_ids).filter(
        dm.Q(expires_at__isnull=True) | dm.Q(expires_at__gt=now)
    )
    group_timer = GroupTimer.objects.filter(is_active=True).first()
    if group_timer and group_timer.is_expired:
        group_timer.is_active = False
        group_timer.save()
        group_timer = None
    group_reading = GroupReadingSession.objects.filter(is_active=True).first()

    return render(request, 'core/dashboard.html', {
        'entries': entries,
        'audio_items': audio_items,
        'video_items': video_items,
        'text_items': text_items,
        'timers': timers,
        'boards': boards,
        'reading': reading,
        'stats': stats,
        'broadcasts': broadcasts,
        'group_timer': group_timer,
        'group_reading': group_reading,
    })


@login_required
@require_POST
def add_entry(request):
    content = request.POST.get('content', '').strip()
    category = request.POST.get('category', 'THOUGHT')
    is_private = request.POST.get('is_private', 'true') != 'false'
    if not content:
        return JsonResponse({'error': 'Content required'}, status=400)
    if category not in ['THOUGHT', 'PRAYER', 'GRATITUDE']:
        category = 'THOUGHT'
    entry = Entry.objects.create(
        user=request.user, category=category,
        content=content, is_private=is_private
    )
    if not is_private:
        dispatch_entry_created(entry)
    return JsonResponse({
        'id': entry.id,
        'category': entry.category,
        'category_display': entry.get_category_display(),
        'content': entry.content,
        'created_at': entry.created_at.strftime('%b %d, %H:%M'),
        'is_private': entry.is_private,
    })


@login_required
@require_POST
def mark_prayer_answered(request, pk):
    entry = get_object_or_404(Entry, pk=pk, user=request.user, category='PRAYER')
    entry.is_answered = True
    entry.save()
    return JsonResponse({'status': 'ok'})


@login_required
def library(request):
    user = request.user
    audio = LibraryItem.objects.filter(media_type='AUDIO').filter(Q(owner=user) | Q(access_level='GLOBAL'))
    video = LibraryItem.objects.filter(media_type='VIDEO').filter(Q(owner=user) | Q(access_level='GLOBAL'))
    text = LibraryItem.objects.filter(media_type='TEXT').filter(Q(owner=user) | Q(access_level='GLOBAL'))
    return render(request, 'core/library.html', {'audio': audio, 'video': video, 'text': text})


@login_required
@require_POST
def upload_library_item(request):
    title = request.POST.get('title', '').strip()
    if not title:
        messages.error(request, 'Title is required.')
        return redirect('library')
    media_type = request.POST.get('media_type', 'AUDIO')
    access_level = request.POST.get('access_level', 'PRIVATE')
    description = request.POST.get('description', '')
    total_pages = request.POST.get('total_pages', '').strip()
    f = request.FILES.get('file')
    if not f:
        messages.error(request, 'No file selected.')
        return redirect('library')
    item = LibraryItem.objects.create(
        owner=request.user, title=title, media_type=media_type,
        access_level=access_level, description=description, file=f,
        total_pages=int(total_pages) if total_pages.isdigit() else None
    )
    messages.success(request, f'"{item.title}" added to library.')
    return redirect('library')


@login_required
def vision_boards(request):
    boards = VisionBoard.objects.filter(owner=request.user)
    public_boards = VisionBoard.objects.filter(is_public=True).exclude(owner=request.user)
    return render(request, 'core/vision_boards.html', {
        'boards': boards,
        'public_boards': public_boards,
    })


@login_required
@require_POST
def create_vision_board(request):
    name = request.POST.get('name', '').strip()
    if not name:
        messages.error(request, 'Board name is required.')
        return redirect('vision_boards')
    is_public = 'is_public' in request.POST
    slug = slugify(name)
    base_slug = slug
    counter = 1
    while VisionBoard.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    board = VisionBoard.objects.create(owner=request.user, name=name, slug=slug, is_public=is_public)
    files = request.FILES.getlist('images')
    for i, img_file in enumerate(files):
        caption = request.POST.get(f'caption_{i}', '')
        VisionBoardImage.objects.create(board=board, image=img_file, caption=caption, order=i)
    html_path = generate_vision_board_html(board)
    board.html_file = html_path
    board.save()
    if is_public:
        url = request.build_absolute_uri(f'/media/{html_path}')
        dispatch_vision_board_published(board, url)
    messages.success(request, f'Vision board "{name}" created!')
    return redirect('vision_boards')


@login_required
def view_vision_board(request, slug):
    board = get_object_or_404(VisionBoard, slug=slug)
    if not board.is_public and board.owner != request.user:
        return HttpResponse("Access denied.", status=403)
    if board.html_file:
        import os
        from django.conf import settings as djsettings
        html_path = os.path.join(djsettings.MEDIA_ROOT, board.html_file)
        if os.path.exists(html_path):
            with open(html_path) as f:
                return HttpResponse(f.read())
    return HttpResponse("Board not generated yet.", status=404)


@login_required
def timers_view(request):
    timers = IntentTimer.objects.filter(user=request.user)
    audio_items = LibraryItem.objects.filter(media_type='AUDIO').filter(
        Q(owner=request.user) | Q(access_level='GLOBAL')
    )
    return render(request, 'core/timers.html', {'timers': timers, 'audio_items': audio_items})


@login_required
@require_POST
def create_timer(request):
    title = request.POST.get('title', '').strip()
    if not title:
        messages.error(request, 'Session name required.')
        return redirect('timers')
    duration = request.POST.get('duration', '15')
    duration = int(duration) if duration.isdigit() else 15
    library_id = request.POST.get('library_item', '')
    library_item = LibraryItem.objects.filter(pk=library_id).first() if library_id.isdigit() else None
    IntentTimer.objects.create(
        user=request.user, title=title, duration_minutes=duration,
        library_item=library_item,
        send_to_email='send_email' in request.POST,
        send_to_discord='send_discord' in request.POST,
        send_to_rocketchat='send_rocketchat' in request.POST,
        create_calendar_event='create_calendar' in request.POST,
    )
    messages.success(request, f'Timer "{title}" saved.')
    return redirect('timers')


@login_required
@require_POST
def complete_timer(request, pk):
    timer = get_object_or_404(IntentTimer, pk=pk, user=request.user)
    timer.completed = True
    timer.is_active = False
    timer.save()
    dispatch_timer_complete(timer)
    return JsonResponse({'status': 'ok'})


@login_required
def profile_settings(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    security, _ = UserSecuritySettings.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        profile.personal_email = request.POST.get('personal_email', '')
        profile.discord_id = request.POST.get('discord_id', '')
        profile.rocketchat_id = request.POST.get('rocketchat_id', '')
        profile.notify_email = 'notify_email' in request.POST
        profile.notify_discord = 'notify_discord' in request.POST
        profile.notify_rocketchat = 'notify_rocketchat' in request.POST
        profile.save()
        # Update email on user object too
        new_email = request.POST.get('personal_email', '')
        if new_email and new_email != request.user.email:
            request.user.email = new_email
            request.user.save()
            # Reset email verification
            security.email_verified = False
            security.save()
        messages.success(request, 'Settings saved.')
        return redirect('settings')
    return render(request, 'core/settings.html', {'profile': profile, 'security': security})


@login_required
@require_POST
def reading_update(request, pk):
    item = get_object_or_404(LibraryItem, pk=pk)
    page = request.POST.get('page', '0')
    page = int(page) if page.isdigit() else 0
    progress, _ = ReadingProgress.objects.get_or_create(user=request.user, item=item)
    progress.current_page = page
    progress.save()
    return JsonResponse({'progress_pct': progress.progress_pct, 'current_page': progress.current_page})


@login_required
@require_POST
def delete_entry(request, pk):
    entry = get_object_or_404(Entry, pk=pk, user=request.user)
    entry.delete()
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def edit_entry(request, pk):
    entry = get_object_or_404(Entry, pk=pk, user=request.user)
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'Content required'}, status=400)
    entry.content = content
    entry.save()
    return JsonResponse({'status': 'ok', 'content': entry.content})


from django.contrib.auth import login as auth_login
from .models import RegistrationRequest

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    error = None
    if request.method == 'POST':
        # Rate limiting — max 5 registrations per hour per IP
        attempts = get_registration_attempts(request)
        if len(attempts) >= 5:
            error = 'Too many registration attempts. Please try again in an hour.'
        else:
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '')
            password2 = request.POST.get('password2', '')
            note = request.POST.get('note', '').strip()
            if not username or not password:
                error = 'Username and password are required.'
            elif password != password2:
                error = 'Passwords do not match.'
            elif len(password) < 8:
                error = 'Password must be at least 8 characters.'
            elif User.objects.filter(username=username).exists():
                error = 'That username is already taken.'
            elif email and User.objects.filter(email=email).exists():
                error = 'That email is already registered.'
            else:
                record_registration_attempt(request)
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    is_active=False
                )
                UserProfile.objects.create(user=user, role='PRACTITIONER')
                RegistrationRequest.objects.create(user=user, note=note)
                UserSecuritySettings.objects.create(user=user)
                # Send verification email if email provided
                if email:
                    send_verification_email(user, request)
                return render(request, 'core/register_pending.html', {'username': username})
    return render(request, 'core/register.html', {'error': error})


@login_required
def pending_approvals(request):
    if not request.user.is_superuser and not getattr(request.user, 'profile', None) and request.user.profile.role != 'ARCHITECT':
        return HttpResponse('Access denied.', status=403)
    pending = RegistrationRequest.objects.filter(status='PENDING').select_related('user')
    approved = RegistrationRequest.objects.filter(status='APPROVED').select_related('user').order_by('-reviewed_at')[:10]
    denied = RegistrationRequest.objects.filter(status='DENIED').select_related('user').order_by('-reviewed_at')[:10]
    return render(request, 'core/approvals.html', {
        'pending': pending,
        'approved': approved,
        'denied': denied,
    })


@login_required
@require_POST
def review_registration(request, pk):
    if not request.user.is_superuser and request.user.profile.role != 'ARCHITECT':
        return HttpResponse('Access denied.', status=403)
    from django.utils import timezone
    reg = get_object_or_404(RegistrationRequest, pk=pk)
    action = request.POST.get('action')
    if action == 'approve':
        reg.status = 'APPROVED'
        reg.user.is_active = True
        reg.user.save()
        # notify user via email if set
        if reg.user.email:
            send_email_notification(
                reg.user.email,
                'Your Positive account has been approved',
                f'Welcome {reg.user.username}! Your account has been approved. You can now log in at your Positive server.'
            )
    elif action == 'deny':
        reg.status = 'DENIED'
        reg.user.is_active = False
        reg.user.save()
    reg.reviewed_at = timezone.now()
    reg.reviewed_by = request.user
    reg.save()
    return JsonResponse({'status': reg.status, 'username': reg.user.username})


# ============ TIMER EDIT / DELETE ============

@login_required
@require_POST
def delete_timer(request, pk):
    timer = get_object_or_404(IntentTimer, pk=pk, user=request.user)
    timer.delete()
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def edit_timer(request, pk):
    timer = get_object_or_404(IntentTimer, pk=pk, user=request.user)
    title = request.POST.get('title', '').strip()
    duration = request.POST.get('duration', '').strip()
    if not title:
        return JsonResponse({'error': 'Title required'}, status=400)
    timer.title = title
    timer.duration_minutes = int(duration) if duration.isdigit() else timer.duration_minutes
    timer.send_to_email = request.POST.get('send_email') == 'on'
    timer.send_to_discord = request.POST.get('send_discord') == 'on'
    timer.send_to_rocketchat = request.POST.get('send_rocketchat') == 'on'
    timer.create_calendar_event = request.POST.get('create_calendar') == 'on'
    library_id = request.POST.get('library_item', '')
    timer.library_item = LibraryItem.objects.filter(pk=library_id).first() if library_id.isdigit() else None
    timer.save()
    messages.success(request, f'Timer "{timer.title}" updated.')
    return redirect('timers')


# ============ LIBRARY EDIT / DELETE ============

@login_required
@require_POST
def delete_library_item(request, pk):
    item = get_object_or_404(LibraryItem, pk=pk, owner=request.user)
    item.delete()
    messages.success(request, f'"{item.title}" removed from library.')
    return redirect('library')


@login_required
@require_POST
def edit_library_item(request, pk):
    item = get_object_or_404(LibraryItem, pk=pk, owner=request.user)
    title = request.POST.get('title', '').strip()
    if not title:
        messages.error(request, 'Title is required.')
        return redirect('library')
    item.title = title
    item.description = request.POST.get('description', '')
    item.access_level = request.POST.get('access_level', item.access_level)
    total_pages = request.POST.get('total_pages', '').strip()
    item.total_pages = int(total_pages) if total_pages.isdigit() else None
    item.save()
    messages.success(request, f'"{item.title}" updated.')
    return redirect('library')


# ============ VISION BOARD EDIT / DELETE ============

@login_required
@require_POST
def delete_vision_board(request, slug):
    board = get_object_or_404(VisionBoard, slug=slug, owner=request.user)
    name = board.name
    # Remove generated HTML file if it exists
    if board.html_file:
        import os
        from django.conf import settings as djsettings
        html_path = os.path.join(djsettings.MEDIA_ROOT, board.html_file)
        if os.path.exists(html_path):
            os.remove(html_path)
    board.delete()
    messages.success(request, f'Vision board "{name}" deleted.')
    return redirect('vision_boards')


@login_required
@require_POST
def edit_vision_board(request, slug):
    board = get_object_or_404(VisionBoard, slug=slug, owner=request.user)
    name = request.POST.get('name', '').strip()
    if not name:
        messages.error(request, 'Board name is required.')
        return redirect('vision_boards')
    board.name = name
    board.is_public = 'is_public' in request.POST
    # Handle new images if uploaded
    new_files = request.FILES.getlist('images')
    if new_files:
        # Remove old images
        board.images.all().delete()
        for i, img_file in enumerate(new_files):
            caption = request.POST.get(f'caption_{i}', '')
            VisionBoardImage.objects.create(board=board, image=img_file, caption=caption, order=i)
    # Regenerate HTML
    html_path = generate_vision_board_html(board)
    board.html_file = html_path
    board.save()
    messages.success(request, f'Vision board "{name}" updated.')
    return redirect('vision_boards')


# ============ GROUP FEATURES ============

from .models import BroadcastMessage, BroadcastDismissal, GroupTimer, GroupReadingSession, CommunityPrayer, PrayerSupport
from django.utils import timezone


def group_hub(request):
    """Main group features page."""
    # Active broadcast
    now = timezone.now()
    dismissed_ids = BroadcastDismissal.objects.filter(user=request.user).values_list('broadcast_id', flat=True)
    broadcasts = BroadcastMessage.objects.filter(
        is_active=True
    ).exclude(id__in=dismissed_ids).filter(
        django_models.Q(expires_at__isnull=True) | django_models.Q(expires_at__gt=now)
    )

    # Active group timer
    group_timer = GroupTimer.objects.filter(is_active=True).first()
    if group_timer and group_timer.is_expired:
        group_timer.is_active = False
        group_timer.save()
        group_timer = None

    # Active group reading
    group_reading = GroupReadingSession.objects.filter(is_active=True).first()

    # Community prayers
    prayers = CommunityPrayer.objects.filter(is_active=True)
    my_supports = PrayerSupport.objects.filter(user=request.user).values_list('prayer_id', flat=True)

    # Text library for reading session
    text_items = LibraryItem.objects.filter(media_type='TEXT').filter(
        django_models.Q(owner=request.user) | django_models.Q(access_level='GLOBAL')
    )
    audio_items = LibraryItem.objects.filter(media_type='AUDIO').filter(
        django_models.Q(owner=request.user) | django_models.Q(access_level='GLOBAL')
    )

    is_architect = request.user.is_superuser or getattr(getattr(request.user, 'profile', None), 'role', '') == 'ARCHITECT'

    return render(request, 'core/group_hub.html', {
        'broadcasts': broadcasts,
        'group_timer': group_timer,
        'group_reading': group_reading,
        'prayers': prayers,
        'my_supports': list(my_supports),
        'text_items': text_items,
        'audio_items': audio_items,
        'is_architect': is_architect,
    })


@login_required
def group_hub_view(request):
    return group_hub(request)


@login_required
def group_timer_status(request):
    """Polling endpoint — returns current group timer state."""
    timer = GroupTimer.objects.filter(is_active=True).first()
    if timer and timer.is_expired:
        timer.is_active = False
        timer.save()
        timer = None
    if timer:
        return JsonResponse({
            'active': True,
            'title': timer.title,
            'seconds_remaining': timer.seconds_remaining,
            'duration_minutes': timer.duration_minutes,
            'started_by': timer.started_by.username,
        })
    return JsonResponse({'active': False})


@login_required
@require_POST
def start_group_timer(request):
    is_architect = request.user.is_superuser or getattr(getattr(request.user, 'profile', None), 'role', '') == 'ARCHITECT'
    if not is_architect:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    # Stop any existing timer
    GroupTimer.objects.filter(is_active=True).update(is_active=False)
    title = request.POST.get('title', 'Group Session')
    duration = int(request.POST.get('duration', 15))
    library_id = request.POST.get('library_item', '')
    library_item = LibraryItem.objects.filter(pk=library_id).first() if library_id.isdigit() else None
    timer = GroupTimer.objects.create(
        started_by=request.user,
        title=title,
        duration_minutes=duration,
        start_time=timezone.now(),
        is_active=True,
        library_item=library_item,
    )
    return JsonResponse({
        'status': 'ok',
        'title': timer.title,
        'seconds_remaining': timer.seconds_remaining,
        'duration_minutes': timer.duration_minutes,
    })


@login_required
@require_POST
def stop_group_timer(request):
    is_architect = request.user.is_superuser or getattr(getattr(request.user, 'profile', None), 'role', '') == 'ARCHITECT'
    if not is_architect:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    GroupTimer.objects.filter(is_active=True).update(is_active=False)
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def send_broadcast(request):
    is_architect = request.user.is_superuser or getattr(getattr(request.user, 'profile', None), 'role', '') == 'ARCHITECT'
    if not is_architect:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    message = request.POST.get('message', '').strip()
    if not message:
        return JsonResponse({'error': 'Message required'}, status=400)
    # Deactivate previous broadcasts
    BroadcastMessage.objects.filter(is_active=True).update(is_active=False)
    broadcast = BroadcastMessage.objects.create(author=request.user, message=message)
    return JsonResponse({'status': 'ok', 'id': broadcast.id, 'message': broadcast.message})


@login_required
@require_POST
def dismiss_broadcast(request, pk):
    broadcast = get_object_or_404(BroadcastMessage, pk=pk)
    BroadcastDismissal.objects.get_or_create(user=request.user, broadcast=broadcast)
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def start_group_reading(request):
    is_architect = request.user.is_superuser or getattr(getattr(request.user, 'profile', None), 'role', '') == 'ARCHITECT'
    if not is_architect:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    GroupReadingSession.objects.filter(is_active=True).update(is_active=False)
    item_id = request.POST.get('library_item', '')
    note = request.POST.get('note', '')
    page = request.POST.get('page', '1')
    item = get_object_or_404(LibraryItem, pk=item_id)
    session = GroupReadingSession.objects.create(
        started_by=request.user,
        library_item=item,
        current_page=int(page) if page.isdigit() else 1,
        note=note,
    )
    return JsonResponse({'status': 'ok', 'title': item.title, 'page': session.current_page})


@login_required
@require_POST
def update_group_reading(request):
    is_architect = request.user.is_superuser or getattr(getattr(request.user, 'profile', None), 'role', '') == 'ARCHITECT'
    if not is_architect:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    session = GroupReadingSession.objects.filter(is_active=True).first()
    if not session:
        return JsonResponse({'error': 'No active session'}, status=404)
    page = request.POST.get('page', '')
    note = request.POST.get('note', '')
    if page.isdigit():
        session.current_page = int(page)
    if note:
        session.note = note
    session.save()
    return JsonResponse({'status': 'ok', 'page': session.current_page})


@login_required
@require_POST
def stop_group_reading(request):
    is_architect = request.user.is_superuser or getattr(getattr(request.user, 'profile', None), 'role', '') == 'ARCHITECT'
    if not is_architect:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    GroupReadingSession.objects.filter(is_active=True).update(is_active=False)
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def add_community_prayer(request):
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'Content required'}, status=400)
    prayer = CommunityPrayer.objects.create(author=request.user, content=content)
    return JsonResponse({
        'status': 'ok',
        'id': prayer.id,
        'content': prayer.content,
        'author': prayer.author.username,
        'created_at': prayer.created_at.strftime('%b %d, %H:%M'),
        'prayer_count': 0,
    })


@login_required
@require_POST
def support_prayer(request, pk):
    prayer = get_object_or_404(CommunityPrayer, pk=pk)
    support, created = PrayerSupport.objects.get_or_create(user=request.user, prayer=prayer)
    if not created:
        support.delete()
        supporting = False
    else:
        supporting = True
    return JsonResponse({'status': 'ok', 'supporting': supporting, 'count': prayer.prayer_count})


@login_required
@require_POST
def answer_community_prayer(request, pk):
    prayer = get_object_or_404(CommunityPrayer, pk=pk)
    if prayer.author != request.user and not request.user.is_superuser:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    prayer.is_answered = True
    prayer.answered_at = timezone.now()
    prayer.save()
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def delete_community_prayer(request, pk):
    prayer = get_object_or_404(CommunityPrayer, pk=pk)
    if prayer.author != request.user and not request.user.is_superuser:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    prayer.delete()
    return JsonResponse({'status': 'ok'})


# Fix the import at top
import django.db.models as django_models


# ============ PASSWORD CHANGE & AVATAR ============

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm


@login_required
def change_password(request):
    if request.method == 'POST':
        old = request.POST.get('old_password', '')
        new1 = request.POST.get('new_password1', '')
        new2 = request.POST.get('new_password2', '')
        error = None
        if not request.user.check_password(old):
            error = 'Current password is incorrect.'
        elif new1 != new2:
            error = 'New passwords do not match.'
        elif len(new1) < 8:
            error = 'Password must be at least 8 characters.'
        else:
            request.user.set_password(new1)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password changed successfully.')
            return redirect('settings')
        messages.error(request, error)
    return redirect('settings')


@login_required
@require_POST
def update_avatar(request):
    color = request.POST.get('color', '#00d4a0')
    initial = request.POST.get('initial', request.user.username[:2].upper())
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    # Store avatar preferences in profile
    profile.avatar_initial = initial[:2].upper()
    profile.save()
    # Store color in session
    request.session['avatar_color'] = color
    return JsonResponse({'status': 'ok', 'initial': profile.avatar_initial, 'color': color})


# ============ SECURITY FEATURES ============

from .models import EmailVerificationToken, TwoFactorCode, UserSecuritySettings
import random
import string
import zipfile
import json
import io
from django.utils import timezone as tz


# ── Email Verification ──

def send_verification_email(user, request):
    token, _ = EmailVerificationToken.objects.get_or_create(user=user)
    token.token = __import__('uuid').uuid4()
    token.verified = False
    token.save()
    verify_url = request.build_absolute_uri(f'/verify-email/{token.token}/')
    send_email_notification(
        user.email,
        'Verify your Positive account email',
        f'Hello {user.username},\n\nPlease verify your email address by clicking the link below:\n\n{verify_url}\n\nThis link is valid for 24 hours.\n\n— Positive'
    )


@login_required
def verify_email_request(request):
    if not request.user.email:
        messages.error(request, 'Please add an email address in Settings first.')
        return redirect('settings')
    send_verification_email(request.user, request)
    messages.success(request, 'Verification email sent. Check your inbox.')
    return redirect('settings')


def verify_email_confirm(request, token):
    try:
        vtoken = EmailVerificationToken.objects.get(token=token)
        vtoken.verified = True
        vtoken.save()
        sec, _ = UserSecuritySettings.objects.get_or_create(user=vtoken.user)
        sec.email_verified = True
        sec.save()
        messages.success(request, 'Email verified successfully!')
    except EmailVerificationToken.DoesNotExist:
        messages.error(request, 'Invalid or expired verification link.')
    return redirect('settings')


# ── Rate Limiting ──

def get_registration_attempts(request):
    """Simple session-based rate limiting for registration."""
    attempts = request.session.get('reg_attempts', [])
    now = tz.now().timestamp()
    # Keep only attempts in last hour
    attempts = [t for t in attempts if now - t < 3600]
    request.session['reg_attempts'] = attempts
    return attempts


def record_registration_attempt(request):
    attempts = get_registration_attempts(request)
    attempts.append(tz.now().timestamp())
    request.session['reg_attempts'] = attempts


# ── Two Factor Authentication ──

def generate_2fa_code():
    return ''.join(random.choices(string.digits, k=6))


def send_2fa_code(user):
    code = generate_2fa_code()
    TwoFactorCode.objects.create(user=user, code=code)
    if user.email:
        send_email_notification(
            user.email,
            'Your Positive login code',
            f'Your login verification code is: {code}\n\nThis code expires in 10 minutes.\n\nIf you did not request this, someone may be trying to access your account.\n\n— Positive'
        )
    return code


@login_required
@require_POST
def toggle_2fa(request):
    sec, _ = UserSecuritySettings.objects.get_or_create(user=request.user)
    if not request.user.email:
        return JsonResponse({'error': 'You need an email address to enable 2FA.'}, status=400)
    sec.two_factor_enabled = not sec.two_factor_enabled
    sec.save()
    status = 'enabled' if sec.two_factor_enabled else 'disabled'
    messages.success(request, f'Two-factor authentication {status}.')
    return JsonResponse({'status': 'ok', 'enabled': sec.two_factor_enabled})


def verify_2fa(request):
    """2FA verification page shown after login."""
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        user_id = request.session.get('2fa_user_id')
        if not user_id:
            return redirect('login')
        try:
            user = User.objects.get(pk=user_id)
            valid_code = TwoFactorCode.objects.filter(
                user=user, code=code, used=False
            ).order_by('-created_at').first()
            if valid_code and valid_code.is_valid():
                valid_code.used = True
                valid_code.save()
                from django.contrib.auth import login as auth_login
                auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                del request.session['2fa_user_id']
                return redirect('dashboard')
            else:
                return render(request, 'core/verify_2fa.html', {'error': 'Invalid or expired code. Please try again.'})
        except User.DoesNotExist:
            return redirect('login')
    return render(request, 'core/verify_2fa.html', {})


# ── Data Export ──

@login_required
def export_data(request):
    """Export all user data as a ZIP file."""
    user = request.user
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:

        # Entries (thoughts, prayers, gratitude)
        entries = Entry.objects.filter(user=user).values(
            'category', 'content', 'is_private', 'is_answered', 'created_at'
        )
        entries_data = []
        for e in entries:
            e['created_at'] = e['created_at'].isoformat()
            entries_data.append(e)
        zf.writestr('entries.json', json.dumps(entries_data, indent=2))

        # Timers
        timers = IntentTimer.objects.filter(user=user).values(
            'title', 'duration_minutes', 'completed', 'created_at'
        )
        timers_data = []
        for t in timers:
            t['created_at'] = t['created_at'].isoformat()
            timers_data.append(t)
        zf.writestr('timers.json', json.dumps(timers_data, indent=2))

        # Vision boards
        boards = VisionBoard.objects.filter(owner=user).values(
            'name', 'slug', 'is_public', 'created_at'
        )
        boards_data = []
        for b in boards:
            b['created_at'] = b['created_at'].isoformat()
            boards_data.append(b)
        zf.writestr('vision_boards.json', json.dumps(boards_data, indent=2))

        # Reading progress
        reading = ReadingProgress.objects.filter(user=user).select_related('item')
        reading_data = []
        for r in reading:
            reading_data.append({
                'title': r.item.title,
                'current_page': r.current_page,
                'total_pages': r.item.total_pages,
                'progress_pct': r.progress_pct,
                'last_read': r.last_read.isoformat(),
            })
        zf.writestr('reading_progress.json', json.dumps(reading_data, indent=2))

        # Profile info
        profile = getattr(user, 'profile', None)
        profile_data = {
            'username': user.username,
            'email': user.email,
            'date_joined': user.date_joined.isoformat(),
            'role': profile.role if profile else 'PRACTITIONER',
        }
        zf.writestr('profile.json', json.dumps(profile_data, indent=2))

        # README
        zf.writestr('README.txt',
            f'Positive Data Export\n'
            f'User: {user.username}\n'
            f'Exported: {tz.now().strftime("%Y-%m-%d %H:%M UTC")}\n\n'
            f'Files:\n'
            f'  entries.json — All thoughts, prayers, and gratitude entries\n'
            f'  timers.json — Your intent timers\n'
            f'  vision_boards.json — Your vision boards\n'
            f'  reading_progress.json — Your reading progress\n'
            f'  profile.json — Your profile information\n'
        )

    buffer.seek(0)
    filename = f'positive_export_{user.username}_{tz.now().strftime("%Y%m%d")}.zip'
    response = HttpResponse(buffer.read(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ============ SEARCH ============

@login_required
def search_entries(request):
    query = request.GET.get('q', '').strip()
    category = request.GET.get('cat', '')
    results = []
    if query:
        from django.db.models import Q
        filters = Q(content__icontains=query) & (Q(user=request.user) | Q(is_private=False))
        if category in ['THOUGHT', 'PRAYER', 'GRATITUDE']:
            filters &= Q(category=category)
        results = Entry.objects.filter(filters).order_by('-created_at')
    return render(request, 'core/search.html', {
        'query': query,
        'category': category,
        'results': results,
        'result_count': len(results),
    })


# ============ READING REMINDERS ============

from .models import ReadingReminder


@login_required
def reading_reminders(request):
    reminders = ReadingReminder.objects.filter(user=request.user)
    text_items = LibraryItem.objects.filter(
        media_type='TEXT'
    ).filter(
        django_models.Q(owner=request.user) | django_models.Q(access_level='GLOBAL')
    )
    return render(request, 'core/reading_reminders.html', {
        'reminders': reminders,
        'text_items': text_items,
    })


@login_required
@require_POST
def create_reading_reminder(request):
    item_id = request.POST.get('library_item', '')
    frequency = request.POST.get('frequency', 'DAILY')
    reminder_time = request.POST.get('reminder_time', '09:00')
    duration = request.POST.get('duration_minutes', '20')
    item = get_object_or_404(LibraryItem, pk=item_id)
    ReadingReminder.objects.create(
        user=request.user,
        library_item=item,
        frequency=frequency,
        reminder_time=reminder_time,
        duration_minutes=int(duration) if duration.isdigit() else 20,
    )
    messages.success(request, f'Reading reminder set for {item.title}.')
    return redirect('reading_reminders')


@login_required
@require_POST
def delete_reading_reminder(request, pk):
    reminder = get_object_or_404(ReadingReminder, pk=pk, user=request.user)
    reminder.delete()
    messages.success(request, 'Reading reminder removed.')
    return redirect('reading_reminders')


# ─── OIDC / SSO ───────────────────────────────────────────────
from authlib.integrations.django_client import OAuth as DjangoOAuth

_oauth = DjangoOAuth()
_authentik = None

def _get_oauth_client():
    global _authentik
    if _authentik is None:
        import os
        _authentik = _oauth.register(
            name='authentik',
            client_id=os.environ.get('OIDC_CLIENT_ID', ''),
            client_secret=os.environ.get('OIDC_CLIENT_SECRET', ''),
            server_metadata_url=os.environ.get('OIDC_DISCOVERY_URL', ''),
            client_kwargs={'scope': 'openid email profile'},
        )
    return _authentik


def oidc_login(request):
    import os
    if not os.environ.get('OIDC_CLIENT_ID'):
        from django.contrib import messages
        messages.warning(request, 'SSO not configured.')
        return redirect('login')
    client = _get_oauth_client()
    redirect_uri = os.environ.get('OIDC_REDIRECT_URI', request.build_absolute_uri('/auth/oidc/callback'))
    return client.authorize_redirect(request, redirect_uri)


def oidc_callback(request):
    import os
    from django.contrib.auth.models import User
    from django.contrib.auth import login as auth_login
    try:
        client = _get_oauth_client()
        token = client.authorize_access_token(request)
        userinfo = token.get('userinfo') or client.userinfo(request)
    except Exception as e:
        from django.contrib import messages
        messages.error(request, 'SSO login failed. Please try again.')
        return redirect('login')

    sub      = userinfo.get('sub', '')
    email    = userinfo.get('email', '')
    username = userinfo.get('preferred_username', sub[:32])

    # Find or create user
    user = User.objects.filter(username=f'sso_{sub[:24]}').first()
    if not user:
        user = User.objects.filter(email=email).first()
        if not user:
            base = username[:28].replace(' ', '_')
            candidate = base
            n = 1
            while User.objects.filter(username=candidate).exists():
                candidate = f'{base}{n}'
                n += 1
            user = User.objects.create_user(
                username=candidate,
                email=email,
                password=None,
            )
            user.set_unusable_password()
            # Auto-approve SSO users
            from core.models import UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = 'PRACTITIONER'
            profile.save()
        user.save()

    if not user.is_active:
        from django.contrib import messages
        messages.error(request, 'Your account is not active.')
        return redirect('login')

    auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    return redirect('dashboard')


# ─── Custom login view to pass oidc_enabled ───────────────────
from django.contrib.auth.views import LoginView as BaseLoginView
import os

class CustomLoginView(BaseLoginView):
    template_name = 'core/login.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['oidc_enabled'] = bool(os.environ.get('OIDC_CLIENT_ID'))
        return ctx
