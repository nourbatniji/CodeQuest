from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect



# decorator = function that wraps another function to add extra behavior
# here we want to wrap views to check if the user is staff/superuser before allowing them into the view

def staff_or_superuser_required(view_func):
    @wraps(view_func)
    # @wraps => makes the decorator function look like the original function, without it the decorator view loses its name, becomes 'wrapper' instead of 'create_challenge'
    def wrapper(request, *args, **kwargs):
        # *args => accept any number of arguments
        # **kwargs => accept all keywords of arguments

        # 1. User not logged in -> send to login
        if not request.user.is_authenticated:
            return redirect('login')
        
        # 2. User logged but NOT staff -> forbidden
        if not (request.user.is_staff or request.user.is_superuser):
            return HttpResponseForbidden('You are not allowed to do this action.')

        # 3. User is staff/superuser -> allow the view to run
        return view_func(request, *args, **kwargs)
    return wrapper