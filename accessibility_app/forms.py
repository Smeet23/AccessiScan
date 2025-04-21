from django import forms
import requests

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class AccessibilityAnalyzerForm(forms.Form):
    """Form for inputting a URL or raw HTML for accessibility analysis."""
    
    INPUT_CHOICES = [
        ('url', 'URL'),
        ('html', 'HTML'),
    ]
    
    input_type = forms.ChoiceField(
        choices=INPUT_CHOICES,
        widget=forms.RadioSelect(),
        initial='url',
        label='Input Type'
    )
    
    url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter website URL (e.g., https://example.com)',
        }),
        label='Website URL'
    )
    
    html = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Paste your HTML here',
            'rows': 10,
        }),
        label='HTML Content'
    )
    
    def clean(self):
        """
        Validate that either URL or HTML is provided based on the selected input_type.
        """
        cleaned_data = super().clean()
        input_type = cleaned_data.get('input_type')
        url = cleaned_data.get('url')
        html = cleaned_data.get('html')
        
        if input_type == 'url' and not url:
            self.add_error('url', 'Please enter a valid URL when URL input type is selected.')
        
        if input_type == 'html' and not html:
            self.add_error('html', 'Please enter HTML content when HTML input type is selected.')
        
        if input_type == 'url' and url:
            # Optionally, validate that the URL is reachable or properly formatted
            try:
                response = requests.get(url, timeout=5)  # Add timeout to avoid hanging requests
                if response.status_code != 200:
                    self.add_error('url', 'The URL seems to be unavailable or invalid.')
            except requests.exceptions.RequestException:
                self.add_error('url', 'There was an issue connecting to the URL.')

        return cleaned_data
