import subprocess
import tempfile
import json
import os

def analyze_accessibility(input_data, input_type):
    """
    Executes Node.js script to perform accessibility analysis.
    """
    node_script_path = os.path.join('scanner', 'scan_url.js' if input_type == 'url' else 'scan_html.js')

    if not os.path.exists(node_script_path):
        raise Exception(f"Node.js script not found at {node_script_path}")

    try:
        if input_type == 'url':
            result = subprocess.run(['node', node_script_path, input_data], capture_output=True, text=True)
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w') as temp_file:
                temp_file.write(input_data)
                temp_path = temp_file.name

            result = subprocess.run(['node', node_script_path, temp_path], capture_output=True, text=True)
            os.unlink(temp_path)

        if result.returncode != 0:
            raise Exception(f"Error from accessibility scanner: {result.stderr}\n{result.stdout}")

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise Exception(f"Error parsing JSON from accessibility scanner output: {e}")

        # Optional: reformat into your existing format
        summary = {
            "total_violations": len(data["violations"]),
            "critical": sum(1 for v in data["violations"] if v["impact"] == "critical"),
            "serious": sum(1 for v in data["violations"] if v["impact"] == "serious"),
            "moderate": sum(1 for v in data["violations"] if v["impact"] == "moderate"),
            "minor": sum(1 for v in data["violations"] if v["impact"] == "minor"),
        }

        return {
            "summary": summary,
            "violations": data["violations"]
        }
    
    except Exception as e:
        raise Exception(f"An error occurred during accessibility analysis: {str(e)}")
    


# Add to utils.py
import re
from .models import AccessibilityRemediationTip

# Add these functions to your utils.py file

def map_axe_rule_to_issue_type(rule_id):
    """
    Maps axe-core rule IDs to internal issue types
    """
    mapping = {
        'image-alt': 'img_alt',
        'heading-order': 'heading_structure',
        'color-contrast': 'color_contrast',
        'label': 'form_labels',
        'keyboard': 'keyboard_nav',
        'aria-required-attr': 'aria_misuse',
        'aria-roles': 'aria_misuse',
        'aria-valid-attr': 'aria_misuse',
        'document-structure': 'semantic_markup',
        'focus-visible': 'focus_indicator',
        'link-name': 'link_purpose',
        # Add more mappings as needed
    }
    
    return mapping.get(rule_id, 'other')

def generate_remediation_plan(analysis):
    """
    Generate a comprehensive remediation plan from accessibility analysis results.
    
    Args:
        analysis: AccessibilityAnalysis instance
        
    Returns:
        list: List of remediation items with violation info and fix suggestions
    """
    from .models import AccessibilityRemediationTip
    
    # Get violations from analysis
    violations = analysis.violations
    
    remediation_plan = []
    
    for violation in violations:
        # For each node (instance) of this violation
        for node in violation.get('nodes', []):
            # Create a remediation item
            remediation_item = type('RemediationItem', (), {})()
            
            # Store violation info
            remediation_item.violation = type('ViolationInfo', (), {})()
            remediation_item.violation.id = violation.get('id', 'unknown')
            remediation_item.violation.impact = violation.get('impact', 'moderate')
            remediation_item.violation.description = violation.get('description', '')
            remediation_item.violation.help = violation.get('help', '')
            remediation_item.violation.helpUrl = violation.get('helpUrl', '')
            
            # Get HTML snippet
            remediation_item.html_snippet = node.get('html', '')
            
            # Find matching tip from database
            issue_type = map_axe_rule_to_issue_type(violation.get('id', ''))
            
            try:
                tip = AccessibilityRemediationTip.objects.filter(
                    issue_type=issue_type,
                    severity=violation.get('impact', 'moderate')
                ).first()
                
                if not tip:
                    # Try to find any tip for this issue type regardless of severity
                    tip = AccessibilityRemediationTip.objects.filter(
                        issue_type=issue_type
                    ).first()
            except:
                tip = None
            
            # Create tips object
            remediation_item.tips = type('TipsInfo', (), {})()
            
            if tip:
                remediation_item.tips.solution = tip.solution
                remediation_item.tips.code_example_before = tip.code_example_before
                remediation_item.tips.code_example_after = tip.code_example_after
                remediation_item.tips.wcag_reference = tip.wcag_reference
            else:
                # Default tips if none found
                remediation_item.tips.solution = f"Address the {violation.get('impact', 'moderate')} {violation.get('id', '')} issue."
                remediation_item.tips.code_example_before = ""
                remediation_item.tips.code_example_after = ""
                remediation_item.tips.wcag_reference = ""
            
            # Generate suggested fix - THIS IS THE KEY CHANGE
            remediation_item.suggested_fix = generate_code_fix(
                remediation_item.html_snippet,
                violation.get('id', ''),
                violation.get('impact', 'moderate')
            )
            
            remediation_plan.append(remediation_item)
    
    return remediation_plan

def generate_code_fix(html_snippet, violation_id, impact):
    """
    Generate a fixed version of the HTML snippet based on the violation type.
    
    Parameters:
    html_snippet (str): The original HTML code with accessibility issues
    violation_id (str): The axe-core rule ID (e.g., 'image-alt')
    impact (str): The impact level (critical, serious, moderate, minor)
    
    Returns:
    str: The fixed HTML code with accessibility issues resolved
    """
    # Default to original if no fixes can be applied
    fixed_html = html_snippet
    
    # Apply fixes based on common accessibility issues
    if violation_id == 'image-alt':
        # Fix missing alt text on images
        if '<img ' in html_snippet and not 'alt=' in html_snippet:
            fixed_html = html_snippet.replace('<img ', '<img alt="Descriptive alt text" ')
        elif '<img ' in html_snippet and 'alt=""' in html_snippet:
            fixed_html = html_snippet.replace('alt=""', 'alt="Descriptive alt text"')
    
    elif violation_id == 'button-name':
        # Fix buttons with no accessible name
        if '<button' in html_snippet and not 'aria-label' in html_snippet:
            if '>' in html_snippet and '</button>' in html_snippet:
                button_parts = html_snippet.split('>', 1)
                if len(button_parts) > 1 and not button_parts[1].strip():
                    # Empty button
                    fixed_html = button_parts[0] + '>Button Label</button>'
                else:
                    # Button with potentially inadequate text
                    fixed_html = html_snippet
            else:
                fixed_html = html_snippet.replace('<button', '<button aria-label="Button label"')
    
    elif violation_id == 'color-contrast':
        # Suggest stronger contrast class
        if 'style="' in html_snippet:
            fixed_html = html_snippet.replace('style="', 'style="color: #000000; background-color: #ffffff; ')
        else:
            if '<' in html_snippet and '>' in html_snippet:
                tag_end = html_snippet.find('>')
                fixed_html = html_snippet[:tag_end] + ' style="color: #000000; background-color: #ffffff;"' + html_snippet[tag_end:]
            else:
                fixed_html = '<!-- Increase contrast ratio to at least 4.5:1 -->\n' + html_snippet
    
    elif violation_id == 'label':
        # Fix form controls without labels
        if '<input' in html_snippet and not '<label' in html_snippet:
            input_id = "input-example"
            if 'id="' in html_snippet:
                # Extract existing ID if present
                import re
                id_match = re.search(r'id=["\']([^"\']+)["\']', html_snippet)
                if id_match:
                    input_id = id_match.group(1)
            else:
                # Add ID if none exists
                fixed_html = html_snippet.replace('<input', f'<input id="{input_id}"')
            
            # Add label before the input element
            fixed_html = f'<label for="{input_id}">Descriptive Label</label>\n{fixed_html}'
            
    elif violation_id == 'link-name':
        # Fix links with no text
        if '<a ' in html_snippet:
            if '></a>' in html_snippet or "></a>" in html_snippet:
                # Empty link
                fixed_html = html_snippet.replace('></a>', '>Descriptive Link Text</a>')
                fixed_html = fixed_html.replace('></a>', '>Descriptive Link Text</a>')
            elif 'aria-label' not in html_snippet:
                # Link with potentially inadequate text
                link_parts = html_snippet.split('>')
                if len(link_parts) > 1:
                    # Insert aria-label
                    fixed_html = link_parts[0] + ' aria-label="Descriptive Link Purpose">' + '>'.join(link_parts[1:])
    
    elif violation_id in ['list', 'listitem']:
        # Fix improper list markup
        if '<ul>' in html_snippet and '<li>' not in html_snippet:
            fixed_html = html_snippet.replace('<ul>', '<ul>\n  <li>List item</li>\n')
        elif '<ol>' in html_snippet and '<li>' not in html_snippet:
            fixed_html = html_snippet.replace('<ol>', '<ol>\n  <li>List item</li>\n')
            
    elif violation_id in ['table-fake-caption', 'td-headers-attr', 'th-has-data-cells']:
        # Fix table issues
        if '<table' in html_snippet:
            if '<caption' not in html_snippet:
                fixed_html = html_snippet.replace('<table', '<table role="table"')
                tag_end = fixed_html.find('>')
                fixed_html = fixed_html[:tag_end+1] + '\n  <caption>Table Caption</caption>' + fixed_html[tag_end+1:]
            
            if '<th' not in html_snippet and '<thead' not in html_snippet:
                # Add table headers
                row_start = fixed_html.find('<tr')
                if row_start != -1:
                    row_end = fixed_html.find('</tr>', row_start)
                    # Check if we found both the start and end of a row
                    if row_end != -1:
                        # Replace td with th in first row
                        row_content = fixed_html[row_start:row_end]
                        fixed_row = row_content.replace('<td', '<th').replace('</td>', '</th>')
                        fixed_html = fixed_html[:row_start] + fixed_row + fixed_html[row_end:]
            
    elif violation_id == 'document-title':
        # Fix missing document title
        fixed_html = html_snippet.replace('<head>', '<head>\n  <title>Page Title</title>')
    
    elif violation_id == 'heading-order':
        # Fix heading order issues
        import re
        heading_match = re.search(r'<h([1-6])', html_snippet)
        if heading_match:
            current_level = int(heading_match.group(1))
            if current_level > 1:  # If not h1
                fixed_html = html_snippet.replace(f'<h{current_level}', f'<h{current_level-1}')
                fixed_html = fixed_html.replace(f'</h{current_level}>', f'</h{current_level-1}>')
                
    elif violation_id == 'aria-roles':
        # Fix ARIA roles issues
        if 'role=' in html_snippet:
            # Replace invalid role with appropriate one
            fixed_html = re.sub(r'role=["\'][^"\']*["\']', 'role="region"', html_snippet)
        else:
            # Add appropriate role based on element type
            if '<div' in html_snippet:
                fixed_html = html_snippet.replace('<div', '<div role="region"')
            elif '<span' in html_snippet:
                fixed_html = html_snippet.replace('<span', '<span role="text"')
                
    # Add more violation types as needed
    
    # If we couldn't generate a specific fix or the fix is identical to the original
    if fixed_html == html_snippet:
        # Create a default fix with a comment
        element_parts = html_snippet.split('>', 1)
        if len(element_parts) > 1:
            tag_part = element_parts[0] + '>'
            content_part = '>' + element_parts[1] if len(element_parts) > 1 else ''
            fixed_html = f"{tag_part}\n<!-- FIXED: {violation_id} - {impact} impact -->{content_part}"
        else:
            fixed_html = f"<!-- FIXED: {violation_id} - {impact} impact -->\n{html_snippet}"
    
    return fixed_html

def analyze_accessibility(input_data, input_type='url'):
    """
    Analyze accessibility of a URL or HTML content using a headless browser and axe-core.
    This is a simplified mock function. In a real implementation, this would use
    a headless browser like Playwright or Selenium with axe-core integration.
    
    Args:
        input_data: URL or HTML content to analyze
        input_type: 'url' or 'html'
        
    Returns:
        dict: Analysis results including violations and summary
    """
    # This is a mock implementation
    # In a real implementation, this would use axe-core to analyze the page
    
    # Mock data structure based on axe-core output format
    result = {
        "violations": [
            {
                "id": "image-alt",
                "impact": "critical",
                "description": "Images must have alternative text",
                "help": "Images must have alt text",
                "helpUrl": "https://dequeuniversity.com/rules/axe/4.0/image-alt",
                "nodes": [
                    {
                        "html": '<img src="logo.png">',
                        "target": ["img"],
                        "suggestions": ["Add alt attribute to the image"]
                    }
                ]
            },
            {
                "id": "color-contrast",
                "impact": "serious",
                "description": "Elements must have sufficient color contrast",
                "help": "Elements must have sufficient color contrast",
                "helpUrl": "https://dequeuniversity.com/rules/axe/4.0/color-contrast",
                "nodes": [
                    {
                        "html": '<p style="color: #cccccc; background-color: #ffffff;">Low contrast text</p>',
                        "target": ["p"],
                        "suggestions": ["Increase the contrast ratio to at least 4.5:1"]
                    }
                ]
            }
        ],
        "summary": {
            "total_violations": 2,
            "critical": 1,
            "serious": 1,
            "moderate": 0,
            "minor": 0
        }
    }
    
    # In a real implementation, different results would be returned based on the input
    if input_type == 'url' and 'example.com' in input_data:
        # Add a mock violation for example.com
        result["violations"].append({
            "id": "link-name",
            "impact": "moderate",
            "description": "Links must have discernible text",
            "help": "Links must have discernible text",
            "helpUrl": "https://dequeuniversity.com/rules/axe/4.0/link-name",
            "nodes": [
                {
                    "html": '<a href="https://example.com/page"></a>',
                    "target": ["a"],
                    "suggestions": ["Add text content to the link"]
                }
            ]
        })
        result["summary"]["total_violations"] += 1
        result["summary"]["moderate"] += 1
    
    return result