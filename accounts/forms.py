from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser


class StudentSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True, max_length=150)
    last_name = forms.CharField(required=True, max_length=150)
    roll_number = forms.CharField(required=False, max_length=50, label="Student ID / Roll Number")
    grade_level = forms.CharField(required=False, max_length=50, label="Grade / Class")

    class Meta:
        model = CustomUser
        fields = (
            'username', 'first_name', 'last_name', 'email',
            'roll_number', 'grade_level', 'password1', 'password2',
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = CustomUser.Role.STUDENT
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.roll_number = self.cleaned_data.get('roll_number', '')
        user.grade_level = self.cleaned_data.get('grade_level', '')
        if commit:
            user.save()
        return user


class TeacherSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True, max_length=150)
    last_name = forms.CharField(required=True, max_length=150)
    department = forms.CharField(required=False, max_length=100, label="Department / Subject Area")

    class Meta:
        model = CustomUser
        fields = (
            'username', 'first_name', 'last_name', 'email',
            'department', 'password1', 'password2',
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = CustomUser.Role.TEACHER
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.department = self.cleaned_data.get('department', '')
        if commit:
            user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 'bio',
            'profile_picture', 'department', 'roll_number', 'grade_level',
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hide teacher/student-only fields based on the instance's role.
        if self.instance and self.instance.pk:
            if self.instance.is_student:
                self.fields.pop('department', None)
            elif self.instance.is_teacher:
                self.fields.pop('roll_number', None)
                self.fields.pop('grade_level', None)
