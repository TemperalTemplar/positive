from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('approvals/', views.pending_approvals, name='approvals'),
    path('approvals/<int:pk>/review/', views.review_registration, name='review_registration'),
    path('library/', views.library, name='library'),
    path('library/upload/', views.upload_library_item, name='upload_library_item'),
    path('library/reading/<int:pk>/update/', views.reading_update, name='reading_update'),
    path('entries/add/', views.add_entry, name='add_entry'),
    path('entries/<int:pk>/answered/', views.mark_prayer_answered, name='mark_prayer_answered'),
    path('entries/<int:pk>/delete/', views.delete_entry, name='delete_entry'),
    path('entries/<int:pk>/edit/', views.edit_entry, name='edit_entry'),
    path('vision-boards/', views.vision_boards, name='vision_boards'),
    path('vision-boards/create/', views.create_vision_board, name='create_vision_board'),
    path('vision-boards/<slug:slug>/', views.view_vision_board, name='view_vision_board'),
    path('timers/', views.timers_view, name='timers'),
    path('timers/create/', views.create_timer, name='create_timer'),
    path('timers/<int:pk>/complete/', views.complete_timer, name='complete_timer'),
    path('settings/', views.profile_settings, name='settings'),
]
