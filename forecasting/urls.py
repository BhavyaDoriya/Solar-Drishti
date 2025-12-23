from django.urls import path
from . import views

urlpatterns = [
    path('', views.indexview, name='home'),
    # path('predict/', views.predictview, name='predict'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
]