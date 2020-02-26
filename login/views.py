from django.shortcuts import render, redirect, HttpResponse
from django.contrib import messages
from .models import User
import bcrypt

def index(request):
    return render(request, "login/index.html")

def new_user(request):
    return render(request, "login/new-user.html")

def register(request):
    clear_login_session(request)
    errors = User.objects.registration_validator(request.POST)
    if len(errors) > 0:
        for key, value in errors.items():
            messages.error(request, value, extra_tags=key) 
        request.session['first_name'] = request.POST['first-name'] 
        request.session['last_name'] = request.POST['last-name']   
        request.session['birthday'] = request.POST['birthday']  
        request.session['register_email'] = request.POST['email']     
        return redirect("login:new-user")

    encodedpw = request.POST['password'].strip().encode()
    hashedpw = bcrypt.hashpw(encodedpw, bcrypt.gensalt()).decode()
    
    user = User.objects.create(
        first_name=request.POST['first-name'].strip(),
        last_name=request.POST['last-name'].strip(),
        birthday=request.POST['birthday'],
        email=request.POST['email'].strip(),
        password=hashedpw
    )
    clear_registration_session(request)
    request.session['user_id'] = user.id
    return redirect("spotification:home")

def login(request):
    clear_registration_session(request)
    errors = User.objects.login_validator(request.POST)
    if len(errors) > 0:
        for key, value in errors.items():
            messages.error(request, value, extra_tags=key) 
        request.session['login_email'] = request.POST['email']
        return redirect("login:home")
    
    clear_login_session(request)
    request.session['user_id'] = User.objects.get(email=request.POST['email'].strip()).id
    return redirect("spotification:home")

def profile(request):
    if not 'user_id' in request.session:
        return redirect("login:home")

    user=User.objects.get(id=request.session['user_id'])
    context = {
        "user_name" : user.full_name,
        "first_name" : user.first_name,
        "last_name" : user.last_name,
        "email" : user.email,
    }
    return render(request, "login/profile.html", context)

def edit_profile(request):
    if not 'user_id' in request.session:
        return redirect("login:home")    

    user=User.objects.get(id=request.session['user_id'])
    errors = User.objects.edit_user_validator(request.POST, user.id)
    if len(errors) > 0:
        for key, value in errors.items():
            messages.error(request, value, extra_tags=key) 
        return redirect("login:profile")

    user.email = request.POST['email'].strip()
    user.first_name = request.POST['first-name'].strip()
    user.last_name = request.POST['last-name'].strip()
    user.save()

    messages.info(request, "User info changes have been saved.", extra_tags="success")
    return redirect("login:profile")

def edit_password(request):
    if not 'user_id' in request.session:
        return redirect("login:home")

    pm = User.objects.password_match_message(request.POST)
    if pm: 
        messages.error(request, pm, extra_tags="password")
        return redirect("login:profile")

    user = User.objects.get(id=request.session['user_id'])
    encodedpw = request.POST['password'].strip().encode()
    hashedpw = bcrypt.hashpw(encodedpw, bcrypt.gensalt()).decode()
    user.password = hashedpw
    user.save()

    messages.info(request, "Password change has been saved.", extra_tags="success")
    return redirect("login:profile")

def logout(request):

def clear_registration_session(request):
    request.session.pop('first_name', None)
    request.session.pop('last_name', None)
    request.session.pop('birthday', None)
    request.session.pop('register_email', None)

def clear_login_session(request):
    request.session.pop('login_email', None)



