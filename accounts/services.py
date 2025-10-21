from .models import User, Student, Instructor
def assign_role(user_id, role):
    u = User.objects.get(id=user_id)
    u.role = role
    u.save()
    if role == "student" and not hasattr(u, "student"):
        Student.objects.create(user=u)
    if role == "instructor" and not hasattr(u, "instructor"):
        Instructor.objects.create(user=u)
    return u
