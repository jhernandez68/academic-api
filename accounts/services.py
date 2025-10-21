from .models import User, Student, Instructor, Role

def assign_role(user_id, role_name):
    """Asigna un rol a un usuario. El parámetro role_name debe ser el nombre del rol (admin, instructor, student)"""
    from django.shortcuts import get_object_or_404

    u = User.objects.get(id=user_id)
    role_obj = get_object_or_404(Role, name=role_name)
    u.role = role_obj
    u.save()

    if role_name == "student" and not hasattr(u, "student"):
        Student.objects.create(user=u)
    if role_name == "instructor" and not hasattr(u, "instructor"):
        Instructor.objects.create(user=u)

    return u
