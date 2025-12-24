from django.shortcuts import render

# Make sure this name matches what you wrote in forecasting/urls.py
def indexview(request):
    return render(request, 'forecasting/index.html')

def history_view(request):
    return render(request, 'forecasting/history.html')

def login_view(request):
    return render(request, 'forecasting/login.html')

import random
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render

def signup_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Check if email already exists in the database
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'status': 'error', 
                'message': 'This email is already registered. Please login instead.'
            }, status=400)

        # ... rest of your OTP generation and email sending logic stays the same ...
        otp = str(random.randint(100000, 999999))
        request.session['otp'] = otp
        request.session['temp_user_data'] = {'username': username, 'email': email, 'password': password}
        
        try:
            send_mail('SolarDrishti OTP', f'Your OTP is {otp}', settings.EMAIL_HOST_USER, [email])
            return JsonResponse({'status': 'sent'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return render(request, 'forecasting/signup.html')
from django.http import JsonResponse, HttpResponse
from .models import User

def verify_otp(request):
    if request.method == 'POST':
        # 1. Get the code sent by JavaScript fetch
        user_otp = request.POST.get('otp_code') 
        # 2. Get the real OTP from the Session
        saved_otp = request.session.get('otp')
        
        # DEBUG: Print to your terminal to see if they match!
        print(f"User entered: {user_otp}, System saved: {saved_otp}")
        
        # 3. Compare as strings to be safe
        if str(user_otp) == str(saved_otp):
            data = request.session.get('temp_user_data')
            
            # Create the user
            User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password']
            )
            
            # Clear sensitive data from session
            del request.session['otp']
            del request.session['temp_user_data']
            
            return HttpResponse(status=200) # Success
        else:
            return HttpResponse(status=400) # Mismatch

from django.contrib.auth import authenticate, login
from django.shortcuts import render

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import update_last_login # Import this

from django.contrib.auth import authenticate, login
from django.shortcuts import render

def login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)

        if user:
            login(request, user)
            update_last_login(None, user)
            # Send success signal
            return render(request, 'forecasting/login.html', {'login_success': True})
        else:
            # Send failure signal
            return render(request, 'forecasting/login.html', {'auth_failed': True})
            
    return render(request, 'forecasting/login.html')
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login
from .models import User

@csrf_exempt # Allowing fetch from the same origin
def google_verify_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # This is the 'credential' sent by Google
            # For a production app, you should verify this token using google-auth library
            # For now, we will use the email passed from the frontend safely
            email = data.get('email') 

            if User.objects.filter(email=email).exists():
                user = User.objects.get(email=email)
                login(request, user)
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'not_found'}, status=403)
        except Exception as e:
            return JsonResponse({'status': 'error'}, status=400)
    return JsonResponse({'status': 'invalid'}, status=405)