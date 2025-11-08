from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        # If user not logged in
        if user.role != 'admin':
            messages.error(request, "Access denied: Admins only.")
            return redirect('Landing')  # Redirect normal members to their own dashboard
        
        # If everything fine → continue
        return view_func(request, *args, **kwargs)
    return wrapper
  
def member_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        # If user not logged in
        if user.role != 'member':
            messages.error(request, "Access denied: Members only.")
            return redirect('Landing')  # Redirect admins to their own dashboard
        
        # If everything fine → continue
        return view_func(request, *args, **kwargs)
    return wrapper