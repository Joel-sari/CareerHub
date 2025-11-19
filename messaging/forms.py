from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class NewConversationForm(forms.Form):
    """
    Simple form to start a new conversation by searching
    a recipient via username or email and writing the first message.
    """
    recipient_query = forms.CharField(
        label="Recipient",
        widget=forms.TextInput(attrs={
            "placeholder": "Username or email",
            "class": "w-full border rounded-lg p-2"
        }),
    )
    body = forms.CharField(
        label="Message",
        widget=forms.Textarea(attrs={
            "rows": 4,
            "placeholder": "Type your message...",
            "class": "w-full border rounded-lg p-2"
        }),
    )

    def clean_recipient_query(self):
        query = self.cleaned_data["recipient_query"].strip()
        if not query:
            raise forms.ValidationError("Please enter a recipient.")
        return query

    def get_recipient(self):
        """
        Try to find a user by username or email.
        You can later upgrade this to fuzzy search or dropdown.
        """
        query = self.cleaned_data.get("recipient_query")
        try:
            return User.objects.get(username=query)
        except User.DoesNotExist:
            try:
                return User.objects.get(email=query)
            except User.DoesNotExist:
                raise forms.ValidationError(
                    "No user found with that username or email."
                )