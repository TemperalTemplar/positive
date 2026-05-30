from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('verify-email/<uuid:token>/', views.verify_email_confirm, name='verify_email_confirm'),
    path('verify-email/request/', views.verify_email_request, name='verify_email_request'),
    path('2fa/verify/', views.verify_2fa, name='verify_2fa'),
    path('2fa/toggle/', views.toggle_2fa, name='toggle_2fa'),
    path('export/', views.export_data, name='export_data'),
    path('approvals/', views.pending_approvals, name='approvals'),
    path('approvals/<int:pk>/review/', views.review_registration, name='review_registration'),

    # Entries
    path('entries/add/', views.add_entry, name='add_entry'),
    path('entries/<int:pk>/answered/', views.mark_prayer_answered, name='mark_prayer_answered'),
    path('entries/<int:pk>/delete/', views.delete_entry, name='delete_entry'),
    path('entries/<int:pk>/edit/', views.edit_entry, name='edit_entry'),

    # Library
    path('library/', views.library, name='library'),
    path('library/upload/', views.upload_library_item, name='upload_library_item'),
    path('library/<int:pk>/edit/', views.edit_library_item, name='edit_library_item'),
    path('library/<int:pk>/delete/', views.delete_library_item, name='delete_library_item'),
    path('library/reading/<int:pk>/update/', views.reading_update, name='reading_update'),

    # Vision Boards
    path('vision-boards/', views.vision_boards, name='vision_boards'),
    path('vision-boards/create/', views.create_vision_board, name='create_vision_board'),
    path('vision-boards/<slug:slug>/', views.view_vision_board, name='view_vision_board'),
    path('vision-boards/<slug:slug>/edit/', views.edit_vision_board, name='edit_vision_board'),
    path('vision-boards/<slug:slug>/delete/', views.delete_vision_board, name='delete_vision_board'),

    # Timers
    path('timers/', views.timers_view, name='timers'),
    path('timers/create/', views.create_timer, name='create_timer'),
    path('timers/<int:pk>/edit/', views.edit_timer, name='edit_timer'),
    path('timers/<int:pk>/delete/', views.delete_timer, name='delete_timer'),
    path('timers/<int:pk>/complete/', views.complete_timer, name='complete_timer'),

    # Settings
    path('settings/', views.profile_settings, name='settings'),
    path('auth/oidc/login/', views.oidc_login, name='oidc_login'),
    path('auth/oidc/callback', views.oidc_callback, name='oidc_callback'),
    path('search/', views.search_entries, name='search'),
    path('reminders/', views.reading_reminders, name='reading_reminders'),
    path('reminders/create/', views.create_reading_reminder, name='create_reading_reminder'),
    path('reminders/<int:pk>/delete/', views.delete_reading_reminder, name='delete_reading_reminder'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('settings/password/', views.change_password, name='change_password'),
    path('settings/avatar/', views.update_avatar, name='update_avatar'),

    # Group Hub
    path('group/', views.group_hub_view, name='group_hub'),
    path('group/timer/status/', views.group_timer_status, name='group_timer_status'),
    path('group/timer/start/', views.start_group_timer, name='start_group_timer'),
    path('group/timer/stop/', views.stop_group_timer, name='stop_group_timer'),
    path('group/broadcast/send/', views.send_broadcast, name='send_broadcast'),
    path('group/broadcast/<int:pk>/dismiss/', views.dismiss_broadcast, name='dismiss_broadcast'),
    path('group/reading/start/', views.start_group_reading, name='start_group_reading'),
    path('group/reading/update/', views.update_group_reading, name='update_group_reading'),
    path('group/reading/stop/', views.stop_group_reading, name='stop_group_reading'),
    path('group/prayers/add/', views.add_community_prayer, name='add_community_prayer'),
    path('group/prayers/<int:pk>/support/', views.support_prayer, name='support_prayer'),
    path('group/prayers/<int:pk>/answered/', views.answer_community_prayer, name='answer_community_prayer'),
    path('group/prayers/<int:pk>/delete/', views.delete_community_prayer, name='delete_community_prayer'),
]
