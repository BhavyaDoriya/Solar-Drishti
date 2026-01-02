"""
views.py
---------
Central request-handling layer for SolarDrishti.

Responsibilities:
- Authentication & account management
- Solar system CRUD
- Prediction lifecycle (forecast → verify → accuracy)
- UI navigation

NOTE:
Business logic and ML inference are intentionally delegated
to ml/predict.py to keep views thin.
"""

# -------------------------
# Standard library imports
# -------------------------
import json
import random
from datetime import timedelta

# -------------------------
# Third-party imports
# -------------------------
import requests
from decouple import config

# -------------------------
# Django imports
# -------------------------
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.models import update_last_login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction

# -------------------------
# Local app imports
# -------------------------
from .models import SolarSystem, Prediction
from .ml.predict import predict_daily_energy

# Use Django’s configured User model
User = get_user_model()

# =====================================================
# Navigation / Static Views
# =====================================================

def indexview(request):
    """Landing page"""
    return render(request, 'forecasting/index.html')


# =====================================================
# History & Accuracy
# =====================================================

@login_required
def history_view(request):
    """
    Displays prediction history and computes weighted accuracy
    based only on verified (actual_value present) predictions.
    """
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


# =====================================================
# Authentication & Registration
# =====================================================

def signup_view(request):
    """
    Email + OTP based signup.
    User is created only after OTP verification.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')

        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'This email is already registered.'
            }, status=400)

        otp = str(random.randint(100000, 999999))
        request.session['otp'] = otp
        request.session['temp_user_data'] = {
            'username': username,
            'email': email,
            'password': password
        }

        try:
            send_mail(
                'SolarDrishti OTP',
                f'Your OTP is {otp}',
                settings.EMAIL_HOST_USER,
                [email]
            )
            return JsonResponse({'status': 'sent'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return render(request, 'forecasting/signup.html')


def verify_otp(request):
    """Finalizes account creation after OTP match."""
    if request.method == 'POST':
        if request.POST.get('otp_code') == request.session.get('otp'):
            data = request.session.get('temp_user_data')

            User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password']
            )

            del request.session['otp']
            del request.session['temp_user_data']
            return HttpResponse(status=200)

    return HttpResponse(status=400)


def login_view(request):
    """Username + password login"""
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


@csrf_exempt
def google_verify_view(request):
    """
    Google OAuth bridge.
    Creates a user automatically if email does not exist.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip().lower()

            user = User.objects.filter(email__iexact=email).first()
            if not user:
                user = User.objects.create_user(
                    username=email.split('@')[0],
                    email=email,
                    password=None
                )

            login(request, user)
            return JsonResponse({'status': 'success'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'invalid'}, status=405)


# =====================================================
# Profile & Account
# =====================================================

@login_required
def profile_view(request, user_id):
    """Public profile summary"""
    profile_user = get_object_or_404(User, pk=user_id)
    total_insights = Prediction.objects.filter(
        system__user=profile_user
    ).count()

    return render(request, 'forecasting/profile.html', {
        'profile_user': profile_user,
        'total_insights': total_insights
    })


@login_required
def profile_update_view(request):
    """Username / password update"""
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
            messages.success(request, "Profile updated successfully.")
            return redirect('profile_view', user_id=request.user.id)

    return render(request, 'forecasting/update_profile.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def delete_account_view(request):
    request.user.delete()
    return redirect('home')


# =====================================================
# Solar Systems & Prediction Flow
# =====================================================

@login_required
def predictview(request):
    """Main dashboard"""
    systems = SolarSystem.objects.filter(user=request.user)
    return render(request, 'forecasting/predict.html', {'systems': systems})


@login_required
def add_system(request):
    """
    Adds a solar system after validating capacity and
    reverse-geocoding location.
    """
    if request.method == 'POST':
        try:
            size = float(request.POST.get('size'))
            if size <= 0:
                raise ValueError

            api_key = config("OPENWEATHER_API_KEY")
            geo_url = (
                f"http://api.openweathermap.org/geo/1.0/reverse"
                f"?lat={request.POST.get('lat')}&lon={request.POST.get('lon')}"
                f"&limit=1&appid={api_key}"
            )

            try:
                response = requests.get(geo_url).json()
                location_name = f"{response[0]['name']}, {response[0]['country']}"
            except Exception:
                location_name = "Unknown Location"

            SolarSystem.objects.create(
                user=request.user,
                name=request.POST.get('name'),
                system_size=size,
                latitude=request.POST.get('lat'),
                longitude=request.POST.get('lon'),
                location_name=location_name
            )

            messages.success(request, "System added successfully.")

        except ValueError:
            messages.error(request, "Invalid system capacity.")

    return redirect('predict')


@login_required
def remove_system(request, system_id):
    system = get_object_or_404(SolarSystem, id=system_id, user=request.user)
    system.delete()
    messages.success(request, "System removed.")
    return redirect('predict')


@login_required
def run_prediction(request, system_id):
    """
    Core prediction trigger.
    Handles:
    - cycle reset
    - lock enforcement
    - ML inference
    """
    system = get_object_or_404(SolarSystem, id=system_id, user=request.user)
    target = request.GET.get('day', 'tomorrow')

    target_date = timezone.now().date() + (timedelta(days=2) if target == 'day_after' else timedelta(days=1))

    if system.first_use_timestamp:
        days_passed = (timezone.now() - system.first_use_timestamp).days
        if (days_passed >= 7 and not system.is_locked) or days_passed >= 14:
            system.first_use_timestamp = timezone.now()
            system.predictions_in_cycle = 0
            system.actuals_in_cycle = 0
            system.save()

    if system.is_locked:
        messages.warning(request, "Weekly verification required.")
        return redirect('predict')

    if not system.first_use_timestamp:
        system.first_use_timestamp = timezone.now()

    try:
        predicted_kw = predict_daily_energy(system, target_date)
    except Exception:
        messages.error(request, "Forecast data unavailable.")
        return redirect('predict')

    Prediction.objects.create(
        system=system,
        target_date=target_date,
        day_target=target,
        pred_value=round(predicted_kw, 2)
    )

    system.predictions_in_cycle += 1
    system.save()

    messages.success(request, f"Forecast generated for {target_date}.")
    return redirect('predict')


@login_required
def update_actual_power(request, system_id):
    """Unlocks system by recording actual output"""
    if request.method == 'POST':
        system = get_object_or_404(SolarSystem, id=system_id, user=request.user)
        val = float(request.POST.get('actual_val'))

        pred = system.predictions.filter(
            actual_value__isnull=True
        ).latest('timestamp')

        pred.actual_value = val
        pred.save()

        system.actuals_in_cycle += 1
        system.save()

        messages.success(request, "Actual power recorded.")

    return redirect('predict')


@login_required
def manual_update_actual(request):
    """
    Manual verification from history page.
    Uses atomic transaction to keep counters consistent.
    """
    if request.method == "POST":
        try:
            actual_val = float(request.POST.get('actual_val'))
        except (ValueError, TypeError):
            messages.error(request, "Invalid value.")
            return redirect('history_view')

        entry = get_object_or_404(
            Prediction,
            id=request.POST.get('prediction_id'),
            system__user=request.user
        )

        if entry.target_date > timezone.now().date():
            messages.error(request, "Future dates not allowed.")
            return redirect('history_view')

        with transaction.atomic():
            was_pending = entry.actual_value is None
            entry.actual_value = actual_val
            entry.save()

            if was_pending:
                entry.system.actuals_in_cycle += 1
                entry.system.save()

        messages.success(request, "Yield updated.")

    return redirect('history_view')


@login_required
def delete_entry(request, entry_id):
    """Deletes a prediction record owned by the user."""
    if request.method == 'POST':
        entry = get_object_or_404(
            Prediction,
            id=entry_id,
            system__user=request.user
        )
        entry.delete()
        messages.success(request, "Record deleted.")

    return redirect('history_view')
