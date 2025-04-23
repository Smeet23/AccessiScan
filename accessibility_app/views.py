# ======================== Django & Library Imports ========================
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from xhtml2pdf import pisa
import matplotlib.pyplot as plt
import base64
from io import BytesIO

# ======================== App-specific Imports ========================
from .forms import AccessibilityAnalyzerForm, SignupForm
from .models import AccessibilityAnalysis, ScanHistory
from .utils import (
    analyze_accessibility,
    generate_remediation_plan,
    generate_code_fix,
    map_axe_rule_to_issue_type,
)

# ======================== Custom Decorators ========================
def custom_login_required(view_func):
    """
    Custom decorator that redirects unauthenticated users to the login page.
    """
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse('accessibility_app:login'))
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# ======================== Chart Views ========================
@custom_login_required
def chart_page(request, report_id):
    report = get_object_or_404(AccessibilityAnalysis, id=report_id, user=request.user)
    return render(request, "Chart.html", {"report": report})

@custom_login_required
def chart_data(request, report_id):
    report = get_object_or_404(AccessibilityAnalysis, id=report_id, user=request.user)
    severity_counts = {
        "critical": report.get_severity_count("critical"),
        "serious": report.get_severity_count("serious"),
        "moderate": report.get_severity_count("moderate"),
        "minor": report.get_severity_count("minor"),
    }
    return JsonResponse({"severity_counts": severity_counts})

# ======================== Authentication Views ========================
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

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return redirect("accessibility_app:home")
    else:
        form = AuthenticationForm()
    return render(request, "auth/login.html", {"form": form})

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

# ======================== Home View ========================
@custom_login_required
def home(request):
    if request.method == 'POST':
        form = AccessibilityAnalyzerForm(request.POST)
        if form.is_valid():
            input_type = form.cleaned_data['input_type']
            request.session['input_type'] = input_type
            request.session['input_data'] = form.cleaned_data.get(input_type)
            return redirect('accessibility_app:result')
    else:
        form = AccessibilityAnalyzerForm()
    return render(request, 'home.html', {'form': form})

# ======================== Result View ========================
@custom_login_required
def result(request, analysis_id=None):
    """
    Display analysis results and remediation suggestions.
    """
    if analysis_id:
        analysis = get_object_or_404(AccessibilityAnalysis, id=analysis_id, user=request.user)
        input_type, input_data = analysis.input_type, analysis.input_data
    else:
        input_type = request.session.get('input_type')
        input_data = request.session.get('input_data')
        if not input_type or not input_data:
            messages.error(request, 'No data to analyze. Please submit the form first.')
            return redirect('accessibility_app:home')

        try:
            analysis_result = analyze_accessibility(input_data, input_type)
            analysis = AccessibilityAnalysis.objects.create(
                input_type=input_type,
                input_data=input_data,
                result_json=analysis_result,
                user_ip=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                user=request.user
            )
            ScanHistory.objects.create(
                user=request.user,
                url=input_data if input_type == "url" else None,
                html_input=input_data if input_type == "html" else None,
                scan_result=analysis_result,
            )
            request.session.pop('input_type', None)
            request.session.pop('input_data', None)
        except Exception as e:
            messages.error(request, f"An error occurred while analyzing the data: {e}")
            return redirect('accessibility_app:home')

    remediation_plan = generate_remediation_plan(analysis)
    severity = {level: analysis.get_severity_count(level) for level in ['critical', 'serious', 'moderate', 'minor']}
    total_count = sum(severity.values())

    context = {
        'analysis': analysis,
        'input_type': input_type,
        'input_data': input_data,
        'analysis_id': analysis.id,
        'total_violations': analysis.total_violations(),
        **severity,
        'total_count': total_count,
        'score': analysis.calculate_score(),
        'remediation_plan': remediation_plan,
        'view_mode': request.GET.get('view', 'results'),
        'critical_count': severity['critical'],  # backward compatibility
        'serious_count': severity['serious'],
        'moderate_count': severity['moderate'],
        'minor_count': severity['minor'],
    }
    return render(request, 'result.html', context)

@custom_login_required
def remediation_view(request, analysis_id):
    """Redirect to result view with remediation tab active."""
    return redirect(f"{reverse('accessibility_app:result', args=[analysis_id])}?view=remediation")

# ======================== PDF View ========================
@custom_login_required
def generate_pdf(request, analysis_id):
    analysis = get_object_or_404(AccessibilityAnalysis, id=analysis_id)

    fig, ax = plt.subplots()
    labels = ['Critical', 'Serious', 'Moderate', 'Minor']
    counts = [analysis.get_severity_count(label.lower()) for label in labels]
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
        'critical': counts[0],
        'serious': counts[1],
        'moderate': counts[2],
        'minor': counts[3],
        'chart_base64': chart_base64,
        'score': analysis.calculate_score(),
    }

    html_string = render_to_string('pdf_template.html', context)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="accessibility_analysis.pdf"'

    if pisa.CreatePDF(html_string, dest=response).err:
        return HttpResponse("Error generating PDF", status=500)

    return response

# ======================== Profile View ========================
@custom_login_required
def profile_view(request):
    history = AccessibilityAnalysis.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "profile.html", {"user": request.user, "history": history})
