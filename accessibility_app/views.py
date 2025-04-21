from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from xhtml2pdf import pisa

from .forms import AccessibilityAnalyzerForm, SignupForm
from .models import AccessibilityAnalysis, ScanHistory
from .utils import analyze_accessibility

# ======================== AUTHENTICATION VIEWS ========================

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
            messages.error(request, "Signup failed. Please check the errors below. 🚨")
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
            if user is not None:
                login(request, user)
                return redirect("accessibility_app:home")
    else:
        form = AuthenticationForm()
    return render(request, "auth/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("accessibility_app:login")


# @login_required
# def dashboard_view(request):
#     history = AccessibilityAnalysis.objects.filter(user=request.user).order_by('-created_at')
#     return render(request, "dashboard.html", {"history": history})

@login_required
def dashboard_view(request):
    history = AccessibilityAnalysis.objects.filter(user=request.user).order_by('-created_at')

    enriched_history = []
    for report in history:
        enriched_history.append({
            "report": report,
            "critical": report.get_severity_count("critical"),
            "serious": report.get_severity_count("serious"),
            "moderate": report.get_severity_count("moderate"),
            "minor": report.get_severity_count("minor"),
        })

    return render(request, "dashboard.html", {"history": enriched_history})


# ======================== MAIN APP VIEWS ========================

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
            'minor': analysis.get_severity_count('minor')
        }

        return render(request, 'result.html', context)

    except Exception as e:
        messages.error(request, f"An error occurred while analyzing the data: {str(e)}")
        return redirect('accessibility_app:home')


def generate_pdf(request, analysis_id):
    analysis = AccessibilityAnalysis.objects.get(id=analysis_id)

    context = {
        'analysis': analysis,
        'input_data': analysis.input_data,
        'input_type': analysis.input_type,
        'total_violations': analysis.total_violations(),
        'critical': analysis.get_severity_count('critical'),
        'serious': analysis.get_severity_count('serious'),
        'moderate': analysis.get_severity_count('moderate'),
        'minor': analysis.get_severity_count('minor')
    }

    html_string = render_to_string('pdf_template.html', context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="accessibility_analysis.pdf"'

    pisa_status = pisa.CreatePDF(html_string, dest=response)

    if pisa_status.err:
        return HttpResponse("Error generating PDF", status=500)

    return response


@login_required
def profile_view(request):
    user = request.user
    history = AccessibilityAnalysis.objects.filter(user=user).order_by('-created_at')
    
    return render(request, "profile.html", {
        "user": user,
        "history": history
    })
