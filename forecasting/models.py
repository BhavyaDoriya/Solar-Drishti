from django.db import models
from django.utils import timezone

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.conf import settings

class SimpleUserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(username=username, email=self.normalize_email(email))
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None):
        user = self.create_user(username, email, password=password)
        user.is_admin = True
        user.save(using=self._db)
        return user

# MAKE SURE THIS IS NAMED "User"
class User(AbstractBaseUser):
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    password = models.CharField(max_length=128)
    date_joined = models.DateTimeField(default=timezone.now)

    # Required for custom users
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = SimpleUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

    # Internal Django permissions logic
    def has_perm(self, perm, obj=None): return True
    def has_module_perms(self, app_label): return True
    @property
    def is_staff(self): return self.is_admin

# forecasting/models.py
from django.db import models
from django.contrib.auth.models import User

from django.db import models
from django.utils import timezone
from django.conf import settings

class SolarSystem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="systems")
    name = models.CharField(max_length=100)
    system_size = models.FloatField(help_text="Max capacity in kW")
    latitude = models.FloatField()
    longitude = models.FloatField()
    location_name = models.CharField(max_length=255)

    # --- LOGIC FIELDS ---
    # Tracks when the first prediction of the 7-day cycle was made
    first_use_timestamp = models.DateTimeField(null=True, blank=True)
    # Counts how many times they clicked "Predict" this active week
    predictions_in_cycle = models.IntegerField(default=0)
    # Counts how many actual values they have provided this week
    actuals_in_cycle = models.IntegerField(default=0)

    @property
    def is_locked(self):
        """Determines if the user must enter data before predicting again."""
        if not self.first_use_timestamp:
            return False  # Brand new, never used.
            
        now = timezone.now()
        days_passed = (now - self.first_use_timestamp).days
        
        # WEEK 1: Unlimited predictions for the first 7 days of activity
        if days_passed < 7:
            return False
            
        # WEEK 2+: Check if they met the dynamic requirement
        # If they predicted 2+ times, they need 2 actuals. 
        # If they predicted 1 time, they need 1 actual.
        # If they predicted 0 times, they are not locked.
        if self.predictions_in_cycle >= 2:
            requirement = 2
        elif self.predictions_in_cycle == 1:
            requirement = 1
        else:
            return False # No predictions made, no lock applied.
            
        if self.actuals_in_cycle < requirement:
            return True # LOCK: Force user to enter data
            
        return False

class Prediction(models.Model):
    system = models.ForeignKey(SolarSystem, on_delete=models.CASCADE, related_name="predictions")
    # Date the prediction was made
    created_at = models.DateTimeField(auto_now_add=True)
    # The actual date the energy is being predicted for
    target_date = models.DateField() 
    
    day_target = models.CharField(max_length=20) # 'tomorrow' or 'day_after'
    pred_value = models.FloatField()
    actual_value = models.FloatField(null=True, blank=True)

    @property
    def accuracy(self):
        if self.actual_value is not None and self.actual_value > 0:
            # Using (1 - Relative Error) formula
            error = abs(self.pred_value - self.actual_value)
            acc = max(0, 100 - (error / self.actual_value * 100))
            return round(acc, 2)
        return None