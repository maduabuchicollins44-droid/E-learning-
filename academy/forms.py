from django import forms
from django.contrib.auth.models import User
from .models import StudentProfile


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = [
            'matric_number',
            'department',
            'level',
            'phone_number',
            'profile_picture',
            'bio',
        ]
