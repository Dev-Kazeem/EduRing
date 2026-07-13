"""exam_platform URL configuration."""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('exams/', include('exams.urls')),
    path('', views.Home, name="home"),
  #  path('', RedirectView.as_view(pattern_name='accounts:dashboard', permanent=False)),
]
