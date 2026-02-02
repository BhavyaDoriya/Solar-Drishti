import json
import logging
import random
import requests
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import update_last_login
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from decouple import config

from .models import SolarSystem, Prediction
from .ml.predict import predict_next_48h

logger = logging.getLogger(__name__)

User = get_user_model()

# -------------------------
# Navigation
# -------------------------

def indexview(request):
    return render(request, 'forecasting/index.html')


# -------------------------
# History
# -------------------------

@login_required
def history_view(request):
    history_list = Prediction.objects.filter(
        system__user=request.user
    ).order_by('-target_date')

    verified_logs = history_list.filter(actual_value__isnull=False)

    if verified_logs.exists():
        total_actual = sum(p.actual_value for p in verified_logs)
        total_error = sum(abs(p.pred_value - p.actual_value) for p in verified_logs)
        avg_acc = max(0, 100 - (total_error / total_actual * 100)) if total_actual > 0 else 0
    else:
        avg_acc = 0

    return render(request, 'forecasting/history.html', {
        'history_list': history_list,
        'avg_acc': round(avg_acc, 2),
        'system_count': SolarSystem.objects.filter(user=request.user).count()
    })


# -------------------------
# Authentication
# -------------------------

@csrf_exempt
def signup_view(request):
    if request.method != "POST":
        return render(request, 'forecasting/signup.html')

    email = request.POST.get('email')
    username = request.POST.get('username')
    password = request.POST.get('password')

    if User.objects.filter(username=username).exists():
        return JsonResponse({'status': 'error', 'message': 'Username already taken'}, status=400)

    if User.objects.filter(email=email).exists():
        return JsonResponse({'status': 'error', 'message': 'Email already registered'}, status=400)

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
            fail_silently=False,
        )
        return JsonResponse({'status': 'sent'})
    except Exception as e:
        logger.error(f"OTP send failed: {e}")
        return JsonResponse({'status': 'error'}, status=500)


def verify_otp(request):
    if request.method != 'POST':
        return HttpResponse(status=405)

    if request.POST.get('otp_code') == request.session.get('otp'):
        data = request.session.get('temp_user_data')
        if not data:
            return HttpResponse("Session expired", status=400)

        User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )

        request.session.flush()
        return HttpResponse(status=200)

    return HttpResponse("Invalid OTP", status=400)


def login_view(request):
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password')
        )
        if user:
            login(request, user)
            update_last_login(None, user)
            return render(request, 'forecasting/login.html', {'login_success': True})

        return render(request, 'forecasting/login.html', {'auth_failed': True})

    return render(request, 'forecasting/login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('home')


# -------------------------
# Profile
# -------------------------

@login_required
def profile_view(request, user_id):
    profile_user = get_object_or_404(User, pk=user_id)
    total_insights = Prediction.objects.filter(system__user=profile_user).count()

    return render(request, 'forecasting/profile.html', {
        'profile_user': profile_user,
        'total_insights': total_insights
    })


@login_required
def profile_update_view(request):
    if request.method == 'POST':
        new_username = request.POST.get('username')
        new_password = request.POST.get('password')

        if User.objects.filter(username=new_username).exclude(id=request.user.id).exists():
            messages.error(request, "Username already taken.")
        else:
            request.user.username = new_username
            if new_password:
                request.user.set_password(new_password)
                login(request, request.user)
            request.user.save()
            messages.success(request, "Profile updated.")
            return redirect('profile_view', user_id=request.user.id)

    return render(request, 'forecasting/update_profile.html')


# -------------------------
# Solar Systems
# -------------------------

@login_required
def predictview(request):
    systems = SolarSystem.objects.filter(user=request.user)
    return render(request, 'forecasting/predict.html', {'systems': systems})


@login_required
def add_system(request):
    if request.method == "POST":
        try:
            size = float(request.POST.get('size'))
            if size <= 0:
                raise ValueError
        except ValueError:
            messages.error(request, "Invalid system size.")
            return redirect('predict')

        lat = request.POST.get('lat')
        lon = request.POST.get('lon')
        name = request.POST.get('name')

        api_key = config("OPENWEATHER_API_KEY")
        geo_url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={api_key}"

        try:
            response = requests.get(geo_url).json()
            location_name = f"{response[0]['name']}, {response[0]['country']}"
        except Exception:
            location_name = "Unknown Location"

        SolarSystem.objects.create(
            user=request.user,
            name=name,
            system_size=size,
            latitude=lat,
            longitude=lon,
            location_name=location_name
        )

        messages.success(request, "System added successfully.")
    return redirect('predict')


@login_required
def remove_system(request, system_id):
    system = get_object_or_404(SolarSystem, id=system_id, user=request.user)
    system.delete()
    messages.success(request, "System removed.")
    return redirect('predict')


# -------------------------
# Prediction
# -------------------------

@login_required
def run_prediction(request, system_id):
    system = get_object_or_404(SolarSystem, id=system_id, user=request.user)
    target = request.GET.get('day', 'tomorrow')

    target_date = timezone.now().date() + (timedelta(days=2) if target == 'day_after' else timedelta(days=1))

    try:
        _, daily_df = predict_next_48h(system.latitude, system.longitude)

        row = daily_df[daily_df["date"] == target_date]
        if row.empty:
            raise ValueError("Prediction not available")

        predicted_energy = float(row["daily_energy"].iloc[0])
        predicted_kwh = predicted_energy * system.system_size

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    Prediction.objects.create(
        system=system,
        target_date=target_date,
        day_target=target,
        pred_value=round(predicted_kwh, 2)
    )

    return JsonResponse({
        "status": "success",
        "date": target_date.isoformat(),
        "predicted_energy": round(predicted_kwh, 2)
    })


# -------------------------
# Actuals Update
# -------------------------

@login_required
def update_actual_power(request, system_id):
    if request.method == "POST":
        system = get_object_or_404(SolarSystem, id=system_id, user=request.user)
        val = float(request.POST.get('actual_val'))

        latest_pred = system.predictions.filter(
            actual_value__isnull=True
        ).latest('target_date')

        latest_pred.actual_value = val
        latest_pred.save()

        system.actuals_in_cycle += 1
        system.save()

        messages.success(request, "Actual power updated.")

    return redirect('predict')


@login_required
def delete_entry(request, entry_id):
    entry = get_object_or_404(Prediction, id=entry_id, system__user=request.user)
    entry.delete()
    messages.success(request, "Entry deleted.")
    return redirect('history_view')












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