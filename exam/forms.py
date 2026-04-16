from django import forms
from .models import UserProfile


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'image']
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Bio yozing...'
            })
        }