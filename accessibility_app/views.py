from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import AccessibilityAnalyzerForm, SignupForm
from .models import AccessibilityAnalysis, ScanHistory
from .utils import analyze_accessibility
import base64
from io import BytesIO
from xhtml2pdf import pisa
import matplotlib.pyplot as plt
from django.shortcuts import redirect
from django.urls import reverse

def custom_login_required(view_func):
    """
    Custom decorator that redirects unauthenticated users to the login page.
    """
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Redirect to the login page
            return redirect(reverse('accessibility_app:login'))  # Change 'accessibility_app:login' to your login URL name
        return view_func(request, *args, **kwargs)

    return _wrapped_view

# ======================== Chart Page View ========================
@custom_login_required
def chart_page(request, report_id):
    """Render the chart page for a specific report."""
    report = get_object_or_404(AccessibilityAnalysis, id=report_id, user=request.user)
    return render(request, "Chart.html", {"report": report})

@custom_login_required
def chart_data(request, report_id):
    """Provide severity data for a specific report only."""
    report = get_object_or_404(AccessibilityAnalysis, id=report_id, user=request.user)
    severity_counts = {
        "critical": report.get_severity_count("critical"),
        "serious": report.get_severity_count("serious"),
        "moderate": report.get_severity_count("moderate"),
        "minor": report.get_severity_count("minor"),
    }
    return JsonResponse({"severity_counts": severity_counts})

# ======================== Register View ========================
def signup_view(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password1"])
            user.save()
            messages.success(request, "Signup successful! 🎉 You can now log in.")
            return redirect("accessibility_app:login")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = SignupForm()
    return render(request, "auth/register.html", {"form": form})

# ======================== Login View ========================
def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("accessibility_app:home")
    else:
        form = AuthenticationForm()
    return render(request, "auth/login.html", {"form": form})

# ======================== Logout View ========================
@custom_login_required
def logout_view(request):
    logout(request)
    return redirect("accessibility_app:login")

# ======================== Dashboard View ========================
@custom_login_required
def dashboard_view(request):
    history = AccessibilityAnalysis.objects.filter(user=request.user).order_by('-created_at')
    enriched_history = [
        {
            "report": report,
            "critical": report.get_severity_count("critical"),
            "serious": report.get_severity_count("serious"),
            "moderate": report.get_severity_count("moderate"),
            "minor": report.get_severity_count("minor"),
            "score": report.calculate_score(),
        }
        for report in history
    ]
    return render(request, "dashboard.html", {"history": enriched_history})

# ======================== Home Page View ========================

@custom_login_required
def home(request):
    if request.method == 'POST':
        form = AccessibilityAnalyzerForm(request.POST)
        if form.is_valid():
            input_type = form.cleaned_data.get('input_type')
            request.session['input_type'] = input_type

            if input_type == 'url':
                request.session['input_data'] = form.cleaned_data.get('url')
            else:
                request.session['input_data'] = form.cleaned_data.get('html')

            return redirect('accessibility_app:result')
    else:
        form = AccessibilityAnalyzerForm()

    return render(request, 'home.html', {'form': form})

# ======================== Result View ========================

@custom_login_required
def result(request):
    input_type = request.session.get('input_type')
    input_data = request.session.get('input_data')

    if not input_type or not input_data:
        messages.error(request, 'No data to analyze. Please submit the form first.')
        return redirect('accessibility_app:home')

    try:
        # Run accessibility analysis
        analysis_result = analyze_accessibility(input_data, input_type)

        # Save main analysis record
        analysis = AccessibilityAnalysis.objects.create(
            input_type=input_type,
            input_data=input_data,
            result_json=analysis_result,
            user_ip=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            user=request.user if request.user.is_authenticated else None
        )

        # Save to history only if logged in
        if request.user.is_authenticated:
            ScanHistory.objects.create(
                user=request.user,
                url=input_data if input_type == "url" else None,
                html_input=input_data if input_type == "html" else None,
                scan_result=analysis_result,
            )

        # Clear session
        request.session.pop('input_type', None)
        request.session.pop('input_data', None)

        context = {
            'analysis': analysis,
            'input_type': input_type,
            'input_data': input_data,
            'analysis_id': analysis.id,
            'total_violations': analysis.total_violations(),
            'critical': analysis.get_severity_count('critical'),
            'serious': analysis.get_severity_count('serious'),
            'moderate': analysis.get_severity_count('moderate'),
            'minor': analysis.get_severity_count('minor'),
            'score': analysis.calculate_score(),
        }

        return render(request, 'result.html', context)

    except Exception as e:
        messages.error(request, f"An error occurred while analyzing the data: {str(e)}")
        return redirect('accessibility_app:home')

# ======================== Pdf Template View ========================
@custom_login_required
def generate_pdf(request, analysis_id):
    analysis = AccessibilityAnalysis.objects.get(id=analysis_id)

    # Generate chart as base64
    fig, ax = plt.subplots()
    labels = ['Critical', 'Serious', 'Moderate', 'Minor']
    counts = [
        analysis.get_severity_count('critical'),
        analysis.get_severity_count('serious'),
        analysis.get_severity_count('moderate'),
        analysis.get_severity_count('minor')
    ]
    colors = ['#f44336', '#ff9800', '#ffeb3b', '#4caf50']
    ax.pie(counts, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')

    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    chart_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    context = {
        'analysis': analysis,
        'input_data': analysis.input_data,
        'input_type': analysis.input_type,
        'total_violations': analysis.total_violations(),
        'critical': analysis.get_severity_count('critical'),
        'serious': analysis.get_severity_count('serious'),
        'moderate': analysis.get_severity_count('moderate'),
        'minor': analysis.get_severity_count('minor'),
        'chart_base64': chart_base64,
        'score': analysis.calculate_score()
    }

    html_string = render_to_string('pdf_template.html', context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="accessibility_analysis.pdf"'

    pisa_status = pisa.CreatePDF(html_string, dest=response)
    if pisa_status.err:
        return HttpResponse("Error generating PDF", status=500)
    return response

# ======================== Profile Page View ========================
@custom_login_required
def profile_view(request):
    user = request.user
    history = AccessibilityAnalysis.objects.filter(user=user).order_by('-created_at')
    
    return render(request, "profile.html", {
        "user": user,
        "history": history
    })
