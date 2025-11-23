from django.db import models
from django.conf import settings
from django.utils import timezone

# ---------------------------------------------------------
# Conversation model
# ---------------------------------------------------------
# A Conversation represents a direct message "thread"
# between (typically) two users: e.g. a Recruiter and a Job Seeker.
#
# We store participants as a ManyToManyField to the User model,
# which keeps this flexible if we ever want >2 users in a thread.
# ---------------------------------------------------------
class Conversation(models.Model):
    # Many-to-many to the custom User model (accounts.User via AUTH_USER_MODEL)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="conversations"
    )

    # Track when the conversation was created + last updated
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Optional convenience field: when the last message was sent
    last_message_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        #for Django admin / debugging
        users = ", ".join([u.username for u in self.participants.all()])
        return f"Conversation between {users}"

    @staticmethod
    def get_or_create_between(user1, user2):
        """
        Helper method to find an existing conversation between two users,
        or create one if it doesn't exist yet.

        This lets us avoid duplicate threads between the same pair.
        """
        # First, try to find a conversation where BOTH users are participants.
        conversations = Conversation.objects.filter(
            participants=user1
        ).filter(
            participants=user2
        )

        if conversations.exists():
            return conversations.first(), False  # (conversation, created=False)

        # If none was found, create a new one and add both users.
        convo = Conversation.objects.create()
        convo.participants.set([user1, user2])
        return convo, True  # (conversation, created=True)


# ---------------------------------------------------------
# Message model
# ---------------------------------------------------------
# A single message sent inside a Conversation.
# We keep track of:
#  - which conversation it belongs to
#  - who sent it
#  - the text body
#  - timestamps and read flag
# ---------------------------------------------------------
class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        related_name="messages",
        on_delete=models.CASCADE,
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="sent_messages",
        on_delete=models.CASCADE,
    )

    # The actual text content of the message
    body = models.TextField()

    # When this message was created
    created_at = models.DateTimeField(auto_now_add=True)

    # Simple "has the recipient(s) read this yet?" flag
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"From {self.sender.username} at {self.created_at:%Y-%m-%d %H:%M}: {self.body[:30]}..."

    def mark_read(self):
        """Convenience helper to mark a message as read."""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=["is_read"])