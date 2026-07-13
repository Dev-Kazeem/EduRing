from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .forms import StudentSignUpForm, TeacherSignUpForm, ProfileUpdateForm
from .models import CustomUser


def register_landing(request):
    """Let the visitor pick Student or Teacher before showing the signup form."""
    return render(request, 'accounts/register_landing.html')


def register_student(request):
    if request.method == 'POST':
        form = StudentSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome! Your student account has been created Successfully.")
            return redirect('accounts:dashboard')
    else:
        form = StudentSignUpForm()
    return render(request, 'accounts/register.html', {'form': form, 'role': 'Student'})


def register_teacher(request):
    if request.method == 'POST':
        form = TeacherSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome! Your teacher account has been created Successfully.")
            return redirect('accounts:dashboard')
    else:
        form = TeacherSignUpForm()
    return render(request, 'accounts/register.html', {'form': form, 'role': 'Teacher'})


@login_required
def dashboard_redirect(request):
    """Send the logged-in user to the correct dashboard for their role."""
    if request.user.is_teacher:
        return redirect('exams:teacher_dashboard')
    return redirect('exams:student_dashboard')


@login_required
def profile_view(request, username=None):
    if username:
        profile_user = get_object_or_404(CustomUser, username=username)
    else:
        profile_user = request.user
    return render(request, 'accounts/profile.html', {'profile_user': profile_user})


@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'accounts/profile_edit.html', {'form': form})
