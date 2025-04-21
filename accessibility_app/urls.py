from django.urls import path
from . import views

app_name = 'accessibility_app'

urlpatterns = [
    path('', views.home, name='home'),  # Home page with the form
    path('result/', views.result, name='result'),  # Result via session-based view
    path('download/pdf/<int:analysis_id>/', views.generate_pdf, name='generate_pdf'),  # PDF download view
    path("register/", views.signup_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
]
