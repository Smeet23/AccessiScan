from django.urls import path
from . import views

app_name = 'accessibility_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('result/', views.result, name='result'),
    path('result/pdf/<int:analysis_id>/', views.generate_pdf, name='generate_pdf'),
]
