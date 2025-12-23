from django.shortcuts import render

# Make sure this name matches what you wrote in forecasting/urls.py
def indexview(request):
    return render(request, 'forecasting/index.html')

def history_view(request):
    return render(request, 'forecasting/history.html')

def login_view(request):
    return render(request, 'forecasting/login.html')

def signup_view(request):
    return render(request, 'forecasting/signup.html')