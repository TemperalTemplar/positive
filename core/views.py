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

    return render(request, 'core/dashboard.html', {
        'entries': entries,
        'audio_items': audio_items,
        'video_items': video_items,
        'text_items': text_items,
        'timers': timers,
        'boards': boards,
        'reading': reading,
        'stats': stats,
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
    if request.method == 'POST':
        profile.personal_email = request.POST.get('personal_email', '')
        profile.discord_id = request.POST.get('discord_id', '')
        profile.rocketchat_id = request.POST.get('rocketchat_id', '')
        profile.notify_email = 'notify_email' in request.POST
        profile.notify_discord = 'notify_discord' in request.POST
        profile.notify_rocketchat = 'notify_rocketchat' in request.POST
        profile.save()
        messages.success(request, 'Settings saved.')
        return redirect('settings')
    return render(request, 'core/settings.html', {'profile': profile})


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
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_active=False  # inactive until approved
            )
            UserProfile.objects.create(user=user, role='PRACTITIONER')
            RegistrationRequest.objects.create(user=user, note=note)
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
