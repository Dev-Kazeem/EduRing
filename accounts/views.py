from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.utils.http import url_has_allowed_host_and_scheme
from exams.models import ExamAttempt

from .forms import StudentSignUpForm, TeacherSignUpForm, ProfileUpdateForm
from .models import CustomUser


def register_landing(request):
    """Let the visitor pick Student or Teacher before showing the signup form."""
    return render(request, 'accounts/register_landing.html')

def is_staff_user(user):
    return user.is_staff

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

@user_passes_test(is_staff_user)
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



def login_view(request):
    next_url = request.POST.get('next') or request.GET.get('next')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                # Validate next_url to avoid open redirect vulnerabilities
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    return redirect(next_url)
                return redirect('accounts:dashboard')  
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('accounts:login')  # change to wherever you want to redirect after logout



@login_required
def dashboard_redirect(request):
    """Send the logged-in user to the correct dashboard for their role."""
    if request.user.is_teacher:
        return redirect('exams:teacher_dashboard')
    return redirect('exams:student_dashboard')


@login_required
def profile_view(request, username=None):
    attempts = ExamAttempt.objects.filter(
        student=request.user
    ).exclude(status=ExamAttempt.Status.IN_PROGRESS).select_related('exam')
    if username:
        profile_user = get_object_or_404(CustomUser, username=username)
    else:
        profile_user = request.user
    return render(request, 'accounts/profile.html', {'profile_user': profile_user , 'attempts' : attempts})


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
