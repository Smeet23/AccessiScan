from django.core.management.base import BaseCommand
from accessibility_app.models import AccessibilityRemediationTip

class Command(BaseCommand):
    help = 'Populates the database with common accessibility remediation tips'

    def handle(self, *args, **options):
        remediation_tips = [
            # Missing Alt Text
            {
                'issue_type': 'img_alt',
                'severity': 'serious',
                'description': 'Images without alt text are not accessible to screen reader users',
                'solution': 'Add descriptive alt text to all images. If the image is decorative, use alt="".',
                'code_example_before': '<img src="logo.png">',
                'code_example_after': '<img src="logo.png" alt="Company Logo">',
                'wcag_reference': 'WCAG 1.1.1 Non-text Content (Level A)',
            },
            
            # Improper Heading Structure
            {
                'issue_type': 'heading_structure',
                'severity': 'serious',
                'description': 'Skipping heading levels or using headings incorrectly disrupts document structure',
                'solution': 'Use headings in a hierarchical order (h1, then h2, etc.) to properly structure your content',
                'code_example_before': '<h1>Page Title</h1>\n<h3>Subtitle</h3>',
                'code_example_after': '<h1>Page Title</h1>\n<h2>Subtitle</h2>',
                'wcag_reference': 'WCAG 1.3.1 Info and Relationships (Level A)',
            },
            
            # Color Contrast
            {
                'issue_type': 'color_contrast',
                'severity': 'serious',
                'description': 'Text with insufficient color contrast is difficult to read for users with low vision',
                'solution': 'Ensure text has a contrast ratio of at least 4.5:1 for normal text and 3:1 for large text',
                'code_example_before': '<p style="color: #999; background-color: #fff;">Low contrast text</p>',
                'code_example_after': '<p style="color: #595959; background-color: #fff;">Higher contrast text</p>',
                'wcag_reference': 'WCAG 1.4.3 Contrast (Minimum) (Level AA)',
            },
            
            # Missing Form Labels
            {
                'issue_type': 'form_labels',
                'severity': 'critical',
                'description': 'Form inputs without proper labels are not accessible to screen reader users',
                'solution': 'Ensure all form inputs have associated labels that are programmatically connected using the "for" attribute',
                'code_example_before': '<input type="text" id="name" placeholder="Enter your name">',
                'code_example_after': '<label for="name">Name</label>\n<input type="text" id="name">',
                'wcag_reference': 'WCAG 3.3.2 Labels or Instructions (Level A)',
            },
            
            # Keyboard Navigation
            {
                'issue_type': 'keyboard_nav',
                'severity': 'critical',
                'description': 'Some elements cannot be accessed or operated with a keyboard alone',
                'solution': 'Ensure all interactive elements are keyboard accessible and have visible focus indicators',
                'code_example_before': '<div onclick="openMenu()">Menu</div>',
                'code_example_after': '<button onclick="openMenu()" tabindex="0">Menu</button>',
                'wcag_reference': 'WCAG 2.1.1 Keyboard (Level A)',
            },
            
            # ARIA Misuse
            {
                'issue_type': 'aria_misuse',
                'severity': 'moderate',
                'description': 'ARIA attributes are being used incorrectly or on inappropriate elements',
                'solution': 'Use ARIA attributes according to their specifications, and prefer native HTML elements when possible',
                'code_example_before': '<div role="button">Click me</div>',
                'code_example_after': '<button>Click me</button>',
                'wcag_reference': 'WCAG 4.1.2 Name, Role, Value (Level A)',
            },
            
            # Improper Semantic Markup
            {
                'issue_type': 'semantic_markup',
                'severity': 'moderate',
                'description': 'Using non-semantic elements makes content less accessible to screen readers',
                'solution': 'Use semantic HTML elements like <nav>, <main>, <article>, etc. to provide structure to your document',
                'code_example_before': '<div class="navigation">\n  <div class="nav-item">Home</div>\n</div>',
                'code_example_after': '<nav>\n  <ul>\n    <li><a href="#">Home</a></li>\n  </ul>\n</nav>',
                'wcag_reference': 'WCAG 1.3.1 Info and Relationships (Level A)',
            },
            
            # Missing Focus Indicator
            {
                'issue_type': 'focus_indicator',
                'severity': 'serious',
                'description': 'Interactive elements without visible focus indicators are difficult to use for keyboard users',
                'solution': 'Ensure all interactive elements have a visible focus state. Do not remove the outline without providing an alternative',
                'code_example_before': 'a:focus { outline: none; }',
                'code_example_after': 'a:focus { outline: 2px solid #0066cc; }',
                'wcag_reference': 'WCAG 2.4.7 Focus Visible (Level AA)',
            },
            
            # Unclear Link Purpose
            {
                'issue_type': 'link_purpose',
                'severity': 'moderate',
                'description': 'Links with unclear text like "click here" or "read more" are ambiguous to screen reader users',
                'solution': 'Make link text descriptive of its destination. Avoid generic phrases like "click here"',
                'code_example_before': '<a href="/pricing">Click here</a> for pricing information.',
                'code_example_after': '<a href="/pricing">View our pricing information</a>',
                'wcag_reference': 'WCAG 2.4.4 Link Purpose (In Context) (Level A)',
            },
            
            # Generic "Other" category
            {
                'issue_type': 'other',
                'severity': 'moderate',
                'description': 'Various accessibility issues that don\'t fit into other categories',
                'solution': 'Address the specific issue according to WCAG guidelines and best practices for web accessibility',
                'code_example_before': '<!-- Example problematic code would go here -->',
                'code_example_after': '<!-- Example fixed code would go here -->',
                'wcag_reference': 'Various WCAG Guidelines',
            },
        ]
        
        count = 0
        for tip in remediation_tips:
            AccessibilityRemediationTip.objects.get_or_create(
                issue_type=tip['issue_type'],
                severity=tip['severity'],
                defaults={
                    'description': tip['description'],
                    'solution': tip['solution'],
                    'code_example_before': tip['code_example_before'],
                    'code_example_after': tip['code_example_after'],
                    'wcag_reference': tip['wcag_reference'],
                }
            )
            count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully added {count} remediation tips'))