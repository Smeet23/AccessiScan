from django.db import models
import json
from django.utils import timezone

class AccessibilityAnalysis(models.Model):
    """
    Model to store accessibility analysis results
    """
    # Input data
    input_type = models.CharField(max_length=10, choices=[('url', 'URL'), ('html', 'HTML')])
    input_data = models.TextField()
    
    # Analysis results
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
        """Get the summary portion of the result"""
        if isinstance(self.result_json, str):
            # If stored as string, convert to dict
            data = json.loads(self.result_json)
        else:
            data = self.result_json
        
        return data.get('summary', {})
    
    @property
    def violations(self):
        """Get the violations portion of the result"""
        if isinstance(self.result_json, str):
            # If stored as string, convert to dict
            data = json.loads(self.result_json)
        else:
            data = self.result_json
        
        return data.get('violations', [])
    
    def total_violations(self):
        """Get the total number of violations"""
        return self.summary.get('total_violations', 0)
    
    def get_severity_count(self, severity):
        """Get the count for a specific severity level"""
        return self.summary.get(severity, 0)