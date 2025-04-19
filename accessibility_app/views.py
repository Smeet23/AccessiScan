from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.contrib import messages

from .forms import AccessibilityAnalyzerForm
from .utils import analyze_accessibility
from .models import AccessibilityAnalysis

def generate_pdf(request, analysis_id):
    # Retrieve the analysis instance
    analysis = AccessibilityAnalysis.objects.get(id=analysis_id)

    # Prepare the context for rendering the HTML template
    context = {
        'analysis': analysis,
        'input_data': analysis.input_data,
        'input_type': analysis.input_type,
    }

    # Render the HTML template to a string
    html_string = render_to_string('pdf_template.html', context)

    # Convert HTML to PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="accessibility_analysis.pdf"'

    # Create the PDF using xhtml2pdf
    pisa_status = pisa.CreatePDF(html_string, dest=response)
    
    if pisa_status.err:
        return HttpResponse("Error generating PDF", status=500)
    
    return response

def home(request):
    """
    Home page view with the form for URL/HTML input.
    """
    if request.method == 'POST':
        form = AccessibilityAnalyzerForm(request.POST)
        if form.is_valid():
            # Get form data
            input_type = form.cleaned_data.get('input_type')
            
            # Store data in session to pass to the result page
            request.session['input_type'] = input_type
            
            if input_type == 'url':
                request.session['input_data'] = form.cleaned_data.get('url')
            else:  # input_type == 'html'
                request.session['input_data'] = form.cleaned_data.get('html')
                
            # Redirect to the result page
            return redirect('accessibility_app:result')
    else:
        form = AccessibilityAnalyzerForm()
    
    return render(request, 'home.html', {'form': form})

def result(request):
    """
    Result page displaying accessibility analysis results.
    """
    # Check if we have data in the session
    input_type = request.session.get('input_type')
    input_data = request.session.get('input_data')
    
    if not input_type or not input_data:
        messages.error(request, 'No data to analyze. Please submit the form first.')
        return redirect('accessibility_app:home')
    
    # Analyze the data (this would call Claude API in a real implementation)
    analysis_result = analyze_accessibility(input_data, input_type)
    
    # Store the analysis in the database
    analysis = AccessibilityAnalysis.objects.create(
        input_type=input_type,
        input_data=input_data,
        result_json=analysis_result,  # Assuming `analysis_result` is a JSON
    )
    
    # Clear session data after use
    request.session.pop('input_type', None)
    request.session.pop('input_data', None)
    
    context = {
        'analysis': analysis_result,
        'input_type': input_type,
        'input_data': input_data,
        'analysis_id': analysis.id,  # Ensure analysis_id is passed here
    }
    
    return render(request, 'result.html', context)