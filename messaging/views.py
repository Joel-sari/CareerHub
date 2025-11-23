from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.db.models import Max, Q, F
# Create your views here.
from django.contrib import messages as django_messages
from django import forms  # for ValidationError use
from .forms import NewConversationForm
from django.db.models.functions import Coalesce

from django.contrib.auth import get_user_model

from .models import Conversation, Message

User = get_user_model()

# ---------------------------------------------------------
# Inbox view
# ---------------------------------------------------------
# Shows all conversations that the CURRENT user is part of.
# Sorts them so the most recent conversation appears first.
# ---------------------------------------------------------
@login_required
def inbox(request):
    # Fetch all conversations this user participates in
    conversations = (
        Conversation.objects
        .filter(participants=request.user)
        .annotate(
            # Use Coalesce: if Max(...) is None, use the convo's 'created_at' time
            last_msg_time=Coalesce(Max("messages__created_at"), F('created_at'))
        )
        # Now we can just order by the (never-None) last_msg_time
        .order_by("-last_msg_time") 
    )

    # For each conversation, we might want to show the "other" user and unread count.
    # We'll compute that here for convenience.
    convo_data = []
    for convo in conversations:
        if not convo or not convo.pk:
            continue
        # Get all participants except the current user -> "other participants"
        others = convo.participants.exclude(id=request.user.id)
        other = others.first()  # typically just one, but safe if there are more

        # Count unread messages in this conversation that were NOT sent by this user(done by the exclude).
        unread_count = Message.objects.filter(
            conversation=convo,
            is_read=False
        ).exclude(sender=request.user).count()

        #We append to convo_data list a dictionary with convo, other user and unread count
        convo_data.append({
            "conversation": convo,
            "other_user": other,
            "unread_count": unread_count,
        })
    # lastly we render the inbox template with convo_data context
    return render(request, "messaging/inbox.html", {
        "conversations": convo_data,
    })


# ---------------------------------------------------------
# Thread view
# ---------------------------------------------------------
# Shows all messages in a given conversation and allows
# the logged-in user to send a new message into that thread.
# ---------------------------------------------------------
@login_required
def thread(request, pk):
    # Get the conversation OR 404 if it doesn't exist
    convo = get_object_or_404(Conversation, pk=pk)

    # Security: ensure the current user is actually a participant
    if not convo.participants.filter(id=request.user.id).exists():
        raise Http404("You are not part of this conversation.")

    # Mark any messages FROM others as read when the thread is opened
    Message.objects.filter(
        conversation=convo,
        #is_read field is False for unread messages
        is_read=False 
    ).exclude(sender=request.user).update(is_read=True) # is_read set to True for messages not sent by current user

    # Handle new message submission
    if request.method == "POST":
        # Get the message body from the form
        body = request.POST.get("body", "").strip()
        if body:
            Message.objects.create(
                conversation=convo,
                sender=request.user,
                body=body,
            )
        # Update last_message_at when a message is sent
        convo.last_message_at = Message.objects.filter(conversation=convo).latest("created_at").created_at
        convo.save(update_fields=["last_message_at"])

        return redirect("messaging:thread", pk=convo.pk)

    # Fetch all messages in this conversation, ordered oldest -> newest
    msgs = convo.messages.order_by("created_at")

    # Same trick as in inbox: find the "other" user for display
    others = convo.participants.exclude(id=request.user.id)
    other = others.first()

# Render the thread template with conversation and messages
    return render(request, "messaging/thread.html", {
        "conversation": convo,
        "messages": msgs,
        "other_user": other,
    })


# ---------------------------------------------------------
# Start conversation view
# ---------------------------------------------------------
# Entry point for "Message" buttons across the site.
# You pass a user_id (the person you want to message),
# and this:
#   - finds existing conversation between you two
#   - or creates a new one
#   - then redirects you to the thread view.
# ---------------------------------------------------------
@login_required
def start_conversation(request, user_id):
    # You cannot message yourself – that wouldn't make sense here
    if request.user.id == user_id:
        return redirect("messaging:inbox")

    # Try to find the user you want to talk to
    other_user = get_object_or_404(User, pk=user_id)

    # Use our helper on the model to either find or create a Conversation
    convo, created = Conversation.get_or_create_between(request.user, other_user)

    # Optionally, initialize last_message_at if brand new
    if created:
        convo.last_message_at = None
        convo.save(update_fields=["last_message_at"])

    return redirect("messaging:thread", pk=convo.pk)

@login_required
def new_message(request):
    """
    'Compose' screen:
    - GET: show form to pick recipient + write first message
    - POST: find recipient, create/reuse Conversation, create first Message
    """
    if request.method == "POST":
        form = NewConversationForm(request.POST)
        if form.is_valid():
            try:
                recipient = form.get_recipient()
            except forms.ValidationError as e:
                # Attach error to field so it shows up in the form
                form.add_error("recipient_query", e)
            else:
                if recipient == request.user:
                    form.add_error("recipient_query", "You can't message yourself.")
                else:
                    # Reuse existing convo if it already exists between these two
                    convo, _created = Conversation.get_or_create_between(
                        request.user,
                        recipient
                    )

                    # Create first message
                    Message.objects.create(
                        conversation=convo,
                        sender=request.user,
                        body=form.cleaned_data["body"],
                    )

                    # Update last_message_at
                    convo.last_message_at = Message.objects.filter(
                        conversation=convo
                    ).latest("created_at").created_at
                    convo.save(update_fields=["last_message_at"])

                    django_messages.success(request, "Message sent.")
                    return redirect("messaging:thread", pk=convo.pk)
    else:
        form = NewConversationForm()

    return render(request, "messaging/new.html", {"form": form})