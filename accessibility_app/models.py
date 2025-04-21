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
