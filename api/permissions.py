from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsTeacher(BasePermission):
    message = "This endpoint is only available to teacher accounts."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_teacher)


class IsStudent(BasePermission):
    message = "This endpoint is only available to student accounts."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_student)


class IsExamOwner(BasePermission):
    """Object-level permission: only the teacher who created the exam may modify it."""
    message = "You don't own this exam."

    def has_object_permission(self, request, view, obj):
        exam = obj if hasattr(obj, 'teacher') else obj.exam
        return exam.teacher_id == request.user.id


class IsAttemptOwner(BasePermission):
    message = "You don't own this exam attempt."

    def has_object_permission(self, request, view, obj):
        return obj.student_id == request.user.id
