from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class AccessibilityAnalysis(models.Model):
    """
    Model to store accessibility analysis results along with user history.
    """

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # ✅ User link (optional if not logged in)

    # Input data
    input_type = models.CharField(max_length=10, choices=[('url', 'URL'), ('html', 'HTML')])
    input_data = models.TextField()

    # Analysis results (full JSON data)
    result_json = models.JSONField()

    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    user_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Accessibility Analysis"
        verbose_name_plural = "Accessibility Analyses"
        ordering = ['-created_at']

    def __str__(self):
        if self.input_type == 'url':
            return f"Analysis of {self.input_data[:50]}... ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
        else:
            return f"HTML Analysis ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

    @property
    def summary(self):
        """Return the summary portion of the analysis result."""
        return self.result_json.get('summary', {})

    @property
    def violations(self):
        """Return the list of violations from the result."""
        return self.result_json.get('violations', [])

    def total_violations(self):
        """Return the total number of violations."""
        return self.summary.get('total_violations', 0)
    

    def get_severity_count(self, severity):
        """
        Get the number of violations of a specific severity.
        Valid severities: critical, serious, moderate, minor.
        """
        return self.summary.get(severity, 0)
    
    def calculate_score(self):
        """Calculate the accessibility score based on violation severity counts."""
        critical = self.get_severity_count("critical")
        serious = self.get_severity_count("serious")
        moderate = self.get_severity_count("moderate")
        minor = self.get_severity_count("minor")

        score = 100 - (critical * 10 + serious * 5 + moderate * 3 + minor * 1)
        return max(0, min(score, 100))  # Ensure the score is between 0 and 100
    

class ScanHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    url = models.URLField(blank=True, null=True)
    html_input = models.TextField(blank=True, null=True)
    scan_result = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.url or 'HTML Input'}"
    

# Add to models.py
class AccessibilityRemediationTip(models.Model):
    ISSUE_TYPES = [
        ('img_alt', 'Missing Alt Text'),
        ('heading_structure', 'Improper Heading Structure'),
        ('color_contrast', 'Insufficient Color Contrast'),
        ('form_labels', 'Missing Form Labels'),
        ('keyboard_nav', 'Keyboard Navigation Issues'),
        ('aria_misuse', 'ARIA Misuse'),
        ('semantic_markup', 'Improper Semantic Markup'),
        ('focus_indicator', 'Missing Focus Indicator'),
        ('link_purpose', 'Unclear Link Purpose'),
        ('other', 'Other'),
    ]
    
    SEVERITY_LEVELS = [
        ('critical', 'Critical'),
        ('serious', 'Serious'),
        ('moderate', 'Moderate'),
        ('minor', 'Minor'),
    ]
    
    issue_type = models.CharField(max_length=50, choices=ISSUE_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    description = models.TextField(help_text="Description of the issue")
    solution = models.TextField(help_text="How to fix the issue")
    code_example_before = models.TextField(blank=True, help_text="Example of problematic code")
    code_example_after = models.TextField(blank=True, help_text="Example of fixed code")
    wcag_reference = models.CharField(max_length=100, blank=True, help_text="WCAG guideline reference")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_issue_type_display()} - {self.get_severity_display()}"