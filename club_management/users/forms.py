# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import CustomUser
from django.contrib.auth import authenticate

class CustomUserCreationForm(UserCreationForm):
    personal_email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-2 focus:ring-[#560bad] focus:border-[#560bad] block w-full p-3 transition duration-200',
            'placeholder': 'your.email@gmail.com'
        })
    )
    
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-2 focus:ring-[#560bad] focus:border-[#560bad] block w-full p-3 transition duration-200',
            'placeholder': 'Choose a username'
        })
    )
    
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-2 focus:ring-[#560bad] focus:border-[#560bad] block w-full p-3 transition duration-200',
            'placeholder': '••••••••'
        })
    )
    
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-2 focus:ring-[#560bad] focus:border-[#560bad] block w-full p-3 transition duration-200',
            'placeholder': '••••••••'
        })
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'personal_email', 'password1', 'password2']
    
    def clean_personal_email(self):
        personal_email = self.cleaned_data.get('personal_email')
        if CustomUser.objects.filter(personal_email=personal_email).exists():
            raise ValidationError("A user with this personal email already exists.")
        return personal_email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError("A user with this username already exists.")
        return username

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Email or Username",
        widget=forms.TextInput(attrs={
            'class': 'bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-2 focus:ring-[#560bad] focus:border-[#560bad] block w-full p-3 transition duration-200',
            'placeholder': 'Enter your email or username'
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-2 focus:ring-[#560bad] focus:border-[#560bad] block w-full p-3 transition duration-200',
            'placeholder': '••••••••'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        username_input = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username_input and password:
            user = None
            
            # Check if input is email format
            if '@' in username_input:
                # Try to find by personal_email
                try:
                    user_obj = CustomUser.objects.get(personal_email=username_input)
                    user = authenticate(
                        self.request, 
                        username=user_obj.personal_email,
                        password=password
                    )
                except CustomUser.DoesNotExist:
                    # Also check college_email
                    try:
                        user_obj = CustomUser.objects.get(college_email=username_input)
                        user = authenticate(
                            self.request, 
                            username=user_obj.personal_email,
                            password=password
                        )
                    except CustomUser.DoesNotExist:
                        pass
            else:
                # Input is username, try to find by username
                try:
                    user_obj = CustomUser.objects.get(username=username_input)
                    user = authenticate(
                        self.request, 
                        username=user_obj.personal_email,
                        password=password
                    )
                except CustomUser.DoesNotExist:
                    pass
            
            if user is not None:
                self.user_cache = user
            else:
                # Simple, short error message
                raise ValidationError("Invalid email/username or password.")
            
            if self.user_cache is None:
                raise ValidationError("Invalid email/username or password.")
            
            self.confirm_login_allowed(self.user_cache)

        return cleaned_data