from django.core.exceptions import PermissionDenied

def recruiter_required(view_func):
    def _wrapped(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated or getattr(user, "role", None) != "recruiter":
            raise PermissionDenied("Recruiter access required.")
        return view_func(request, *args, **kwargs)
    return _wrapped