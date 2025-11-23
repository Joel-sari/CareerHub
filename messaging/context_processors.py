from .models import Message

def messaging_context(request):
    """
    Makes unread message info available in all templates:
      - unread_message_count
      - unread_message_previews (last 5 unread)
    """
    if not request.user.is_authenticated:
        return {}

    unread_qs = (
        Message.objects
        .filter(conversation__participants=request.user, is_read=False)
        .exclude(sender=request.user)
        .select_related("conversation", "sender")
        .order_by("-created_at")
    )

    return {
        "unread_message_count": unread_qs.count(),
        "unread_message_previews": unread_qs[:5],
    }