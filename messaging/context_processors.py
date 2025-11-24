from .models import Message
from .models import Message, JobNotification

def messaging_context(request):
    """
    Makes unread message + job notification info available in all templates:
      - unread_message_count
      - unread_message_previews (last 5 unread messages)
      - unread_job_notification_count
      - unread_job_notifications (last 5 unread job notifications)
      - unread_notification_total (messages + job notifications)
    """
    if not request.user.is_authenticated:
        return {}

    # Unread messages where the current user is a participant but NOT the sender
    unread_messages_qs = (
        Message.objects
        .filter(conversation__participants=request.user, is_read=False)
        .exclude(sender=request.user)
        .select_related("conversation", "sender")
        .order_by("-created_at")
    )

    # Unread job notifications for this user
    unread_jobs_qs = (
        JobNotification.objects
        .filter(user=request.user, is_read=False)
        .select_related("job")
        .order_by("-created_at")
    )

    unread_message_count = unread_messages_qs.count()
    unread_job_notification_count = unread_jobs_qs.count()
    unread_notification_total = unread_message_count + unread_job_notification_count

    return {
        "unread_message_count": unread_message_count,
        "unread_message_previews": unread_messages_qs[:5],
        "unread_job_notification_count": unread_job_notification_count,
        "unread_job_notifications": unread_jobs_qs[:5],
        "unread_notification_total": unread_notification_total,
    }
