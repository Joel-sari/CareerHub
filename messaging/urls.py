from django.urls import path
from . import views


app_name = "messaging"
urlpatterns = [
    # Inbox page – list of conversations for the logged-in user
    path("", views.inbox, name="inbox"),

    # View a specific conversation thread by ID
    path("<int:pk>/", views.thread, name="thread"),

    # Start a conversation with another user (by user id)
    path("start/<int:user_id>/", views.start_conversation, name="start_conversation"),

    # NEW Message form view
    path("new/", views.new_message, name="new"),

    # Mark all messages in a conversation as read
    path("notifications/mark-all-read/", views.notifications_mark_all_read, name="notifications_mark_all_read"),



]