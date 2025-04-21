from django.contrib import admin
from .models import AccessibilityAnalysis
import json

@admin.register(AccessibilityAnalysis)
class AccessibilityAnalysisAdmin(admin.ModelAdmin):
    list_display = ('id', 'input_type', 'input_data_preview', 'total_violations', 'created_at')
    list_filter = ('input_type', 'created_at')
    search_fields = ('input_data',)
    readonly_fields = ('created_at',)
    
    def input_data_preview(self, obj):
        """Return a preview of the input data"""
        if obj.input_type == 'url':
            return obj.input_data
        else:
            return obj.input_data[:100] + '...' if len(obj.input_data) > 100 else obj.input_data
    
    input_data_preview.short_description = 'Input Data'
    
    def total_violations(self, obj):
        """Return the total number of violations from the result_json"""
        try:
            result_json = json.loads(obj.result_json)  # Assuming result_json is stored as a JSON string
            return result_json.get('summary', {}).get('total_violations', 0)
        except (json.JSONDecodeError, TypeError):
            return 0
    
    total_violations.short_description = 'Total Violations'
