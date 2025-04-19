from django import forms

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
        
        return cleaned_data