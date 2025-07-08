from django import forms
from .models import Message
from django.contrib.auth import get_user_model
User = get_user_model()

from .models import Message

class MessageForm(forms.ModelForm):
    contenido = forms.CharField(
        label="",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control msg-textarea',
            'rows': 3,
            'placeholder': 'Escribe tu mensaje…'
        })
    )

    class Meta:
        model  = Message
        fields = ['contenido']