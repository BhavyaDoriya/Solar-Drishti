import json
import random
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.models import update_last_login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .ml.predict import predict_next_48h
from decouple import config
import random
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .models import User

logger = logging.getLogger(__name__)


# Import your models
from .models import SolarSystem, Prediction

# Correctly define the User model for the entire file
User = get_user_model()

# --- Navigation Views ---

def indexview(request):
    return render(request, 'forecasting/index.html')

from django.db.models import Avg

# @login_required
# def history_view(request):
#     history_list = Prediction.objects.filter(system__user=request.user).order_by('-target_date')
    
#     # FILTER only records that have actual values
#     verified_logs = history_list.filter(actual_value__isnull=False)
    
#     if verified_logs.exists():
#         # Better Precision Logic
#         total_error = sum(abs(p.pred_value - p.actual_value) for p in verified_logs)
#         total_actual = sum(p.actual_value for p in verified_logs)
        
#         if total_actual > 0:
#             avg_acc = max(0, 100 - (total_error / total_actual * 100))
#         else:
#             avg_acc = 0
#     else:
#         avg_acc = 0
    
#     return render(request, 'forecasting/history.html', {
#         'history_list': history_list,
#         'avg_acc': round(avg_acc, 2), # Keep 2 decimal places for accuracy
#         'system_count': SolarSystem.objects.filter(user=request.user).count()
#     })

# --- Authentication & Registration Views ---

@csrf_exempt  # IMPORTANT for AJAX OTP requests on production
def signup_view(request):
    if request.method != "POST":
        return render(request, 'forecasting/signup.html')

    email = request.POST.get('email')
    username = request.POST.get('username')
    password = request.POST.get('password')
    if User.objects.filter(username=username).exists():
            error_msg = "Username already taken. Please choose another."
            # We still add it to the django messages module just in case
            messages.error(request, error_msg) 
            # But we MUST send it in the JSON for the AJAX to show it now
            return JsonResponse({'status': 'error', 'message': error_msg}, status=400)

    logger.info(f"Signup attempt for email: {email}")

    if not email or not username or not password:
        return JsonResponse(
            {'status': 'error', 'message': 'Missing required fields'},
            status=400
        )

    if User.objects.filter(email=email).exists():
        return JsonResponse(
            {
                'status': 'error',
                'message': 'This email is already registered. Please login instead.'
            },
            status=400
        )

    otp = str(random.randint(100000, 999999))

    request.session['otp'] = otp
    request.session['temp_user_data'] = {
        'username': username,
        'email': email,
        'password': password
    }

    try:
        send_mail(
            subject='SolarDrishti OTP',
            message=f'Your OTP is {otp}',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,   # 👈 VERY IMPORTANT
        )

        logger.info(f"OTP email sent successfully to {email}")
        return JsonResponse({'status': 'sent'})

    except Exception as e:
        logger.error(f"OTP email FAILED for {email}: {repr(e)}")

        return JsonResponse(
            {
                'status': 'error',
                'message': 'OTP could not be sent. Please try again later.'
            },
            status=500
        )

def verify_otp(request):
    if request.method == 'POST':
        # Clean both inputs to strings and remove any whitespace
        user_otp = str(request.POST.get('otp_code', '')).strip()
        saved_otp = str(request.session.get('otp', '')).strip()
        
        if user_otp and saved_otp and user_otp == saved_otp:
            data = request.session.get('temp_user_data')
            
            if not data:
                return HttpResponse("Session expired", status=400)

            User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password']
            )
            
            # Cleanup session
            del request.session['otp']
            del request.session['temp_user_data']
            return HttpResponse(status=200)
        else:
            return HttpResponse("Invalid OTP", status=400)
    return HttpResponse(status=405)
def login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)

        if user:
            login(request, user)
            update_last_login(None, user)
            return render(request, 'forecasting/login.html', {'login_success': True})
        else:
            return render(request, 'forecasting/login.html', {'auth_failed': True})
            
    return render(request, 'forecasting/login.html')

@csrf_exempt
def google_verify_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            raw_email = data.get('email', '')
            email = raw_email.strip().lower() 

            user = User.objects.filter(email__iexact=email).first() 

            if not user:
                username = email.split('@')[0] 
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=None
                )
            
            login(request, user)
            return JsonResponse({'status': 'success'})

        except Exception as e:
            print(f"Google Login Error: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'invalid'}, status=405)

# --- Profile & Account Management ---

@login_required
@login_required
def profile_view(request, user_id):
    profile_user = get_object_or_404(User, pk=user_id)
    
    # Count predictions across all systems owned by this user
    # This uses the 'related_name' defined in your models
    total_insights = Prediction.objects.filter(system__user=profile_user).count()
    
    return render(request, 'forecasting/profile.html', {
        'profile_user': profile_user,
        'total_insights': total_insights
    })
@login_required
def profile_update_view(request):
    return render(request, 'forecasting/update_profile.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def delete_account_view(request):
    user = request.user
    user.delete()
    return redirect('home')

# --- Solar Prediction Logic ---

@login_required
def predictview(request):
    systems = SolarSystem.objects.filter(user=request.user)
    return render(request, 'forecasting/predict.html', {'systems': systems})

@login_required
def add_system(request):
    if request.method == "POST":
        lat = request.POST.get('lat')
        lon = request.POST.get('lon')
        name = request.POST.get('name')
        
        try:
            # 1. Convert size to float and check for negative values
            size = float(request.POST.get('size'))
            
            if size <= 0:
                messages.error(request, "System capacity must be a positive number.")
                return redirect('predict')
            
            # 2. OpenWeather Geocoding logic
            api_key = config("OPENWEATHER_API_KEY")
            geo_url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={api_key}"
            
            try:
                response = requests.get(geo_url).json()
                location_name = f"{response[0]['name']}, {response[0]['country']}"
            except:
                location_name = "Unknown Location"

            # 3. Create the system
            SolarSystem.objects.create(
                user=request.user,
                name=name,
                system_size=size,
                latitude=lat,
                longitude=lon,
                location_name=location_name
            )
            messages.success(request, f"System '{name}' added successfully!")
            
        except ValueError:
            messages.error(request, "Please enter a valid number for system capacity.")
            
    return redirect('predict')

@login_required
def remove_system(request, system_id):
    system = get_object_or_404(SolarSystem, id=system_id, user=request.user)
    system.delete()
    messages.success(request, f"System '{system.name}' removed successfully.")
    return redirect('predict')
from datetime import timedelta
from django.utils import timezone
import random


@login_required
def run_prediction(request, system_id):
    system = get_object_or_404(SolarSystem, id=system_id, user=request.user)
    target = request.GET.get('day', 'tomorrow')
    target_date = timezone.now().date() + (timedelta(days=2) if target == 'day_after' else timedelta(days=1))

    try:
        _, daily_df = predict_next_48h(system.latitude, system.longitude)
        row = daily_df[daily_df["date"] == target_date]
        
        if row.empty:
            row = daily_df.iloc[[0]] if not daily_df.empty else None
            if not row: return JsonResponse({'status': 'error', 'message': 'No data'}, status=400)

        predicted_energy = float(row["daily_energy"].iloc[0])
        predicted_kwh = predicted_energy * system.system_size

        # helper to safely grab values from the row
        def get_val(df_row, col_name):
            return float(df_row[col_name].iloc[0]) if col_name in df_row.columns else 0.0

        # MATCHING TERMINAL LOG NAMES: ghi, air_temp, wind_speed
        factors = {
            "ghi": round(get_val(row, "ghi"), 2),
            "temp": round(get_val(row, "air_temp"), 1),
            "wind": round(get_val(row, "wind_speed"), 1),
        }

    except Exception as e:
        logger.error(f"Prediction Error: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    Prediction.objects.create(
        system=system, target_date=target_date, day_target=target,
        pred_value=round(predicted_kwh, 2)
    )

    return JsonResponse({
        "status": "success",
        "date": target_date.isoformat(),
        "predicted_energy": round(predicted_kwh, 2),
        "factors": factors
    })

@login_required
def update_actual_power(request, system_id):
    if request.method == "POST":
        system = get_object_or_404(SolarSystem, id=system_id, user=request.user)
        val = float(request.POST.get('actual_val'))

        # Find the latest prediction that doesn't have an actual value yet
        latest_pred = system.predictions.filter(actual_value__isnull=True).latest('timestamp')
        latest_pred.actual_value = val
        latest_pred.save()

        # Update cycle counter
        system.actuals_in_cycle += 1
        system.save()

        messages.success(request, "Actual power recorded! System status updated.")
    
    return redirect('predict')

@login_required
def profile_update_view(request):
    if request.method == 'POST':
        new_username = request.POST.get('username')
        new_password = request.POST.get('password')
        
        # 1. Update Username
        if User.objects.filter(username=new_username).exclude(id=request.user.id).exists():
            messages.error(request, "Username already taken.")
        else:
            request.user.username = new_username
            
            # 2. Update Password if provided
            if new_password and len(new_password) > 0:
                request.user.set_password(new_password) # Correctly hashes the password
                login(request, request.user) # Re-log the user in after password change
            
            request.user.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile_view', user_id=request.user.id)
            
    return render(request, 'forecasting/update_profile.html')
from django.shortcuts import get_object_or_404, redirect
from .models import Prediction

@login_required
def delete_entry(request, entry_id):
    if request.method == 'POST':
        # Get the entry and ensure it belongs to the user (security check)
        entry = get_object_or_404(Prediction, id=entry_id, system__user=request.user)
        entry.delete()
        messages.success(request, "Record deleted successfully.")
    
    return redirect('history_view') # Make sure this matches your history URL name
from django.utils import timezone

from django.utils import timezone


from django.utils import timezone
from django.db.models import Sum, F
from django.db import transaction


from django.db import transaction

from django.utils import timezone
from django.db import transaction
from django.db.models import Sum

from django.utils import timezone
from django.db import transaction

@login_required
def history_view(request):
    history_list = Prediction.objects.filter(system__user=request.user).order_by('-target_date')
    verified_logs = history_list.filter(actual_value__isnull=False)
    
    if verified_logs.exists():
        # High-precision weighted accuracy calculation
        total_actual = sum(p.actual_value for p in verified_logs)
        total_error = sum(abs(p.pred_value - p.actual_value) for p in verified_logs)
        avg_acc_val = max(0, 100 - (total_error / total_actual * 100)) if total_actual > 0 else 0
    else:
        avg_acc_val = 0
    
    return render(request, 'forecasting/history.html', {
        'history_list': history_list,
        'avg_acc': round(avg_acc_val, 2), # Correctly rounded for summary card
        'system_count': SolarSystem.objects.filter(user=request.user).count()
    })

@login_required
def manual_update_actual(request):
    if request.method == "POST":
        prediction_id = request.POST.get('prediction_id')
        try:
            actual_val = float(request.POST.get('actual_val'))
        except (ValueError, TypeError):
            messages.error(request, "Invalid numeric value.")
            return redirect('history_view')
        
        entry = get_object_or_404(Prediction, id=prediction_id, system__user=request.user)
        
        # VALIDATION: Prevent future dates
        if entry.target_date > timezone.now().date():
            messages.error(request, "You cannot verify output for a future date.")
            return redirect('history_view')

        # DATABASE UPDATE: Using atomic transaction for reliability
        with transaction.atomic():
            was_pending = entry.actual_value is None
            entry.actual_value = actual_val
            entry.save() # Forced database commit
            
            if was_pending:
                system = entry.system
                system.actuals_in_cycle += 1
                system.save()
        
        messages.success(request, f"Yield for {entry.target_date} updated successfully!")
    return redirect('history_view')
def about_view(request):
    return render(request, 'forecasting/about.html')