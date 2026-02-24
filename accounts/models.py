from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from datetime import timedelta

# USER MANAGER - Custom manager for creating users and superusers
class UserManager(BaseUserManager):
    def create_user(self, mobile, password=None, **extra_fields):
        if not mobile:
            raise ValueError('The Mobile number must be set')
        user = self.model(mobile=mobile, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, mobile, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(mobile, password, **extra_fields)


# USER MODEL - Main user table for authentication
class User(AbstractBaseUser, PermissionsMixin):
    mobile = models.CharField(max_length=15, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    onboarding_completed = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'mobile'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.mobile
    
    class Meta:
        verbose_name = "User / Admin"
        verbose_name_plural = "Users"


# OTP MODEL - Stores one-time passwords for mobile verification
class OTP(models.Model):
    mobile = models.CharField(max_length=15)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        """OTP expires after 15 minutes"""
        expiry_time = self.created_at + timedelta(minutes=15)
        return timezone.now() > expiry_time

    def __str__(self):
        return f"{self.mobile} - {self.code}"
    
    class Meta:
        verbose_name = "OTP"
        verbose_name_plural = "OTPs"


# LOGIN HISTORY - Tracks all user login attempts
class LoginHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_name = models.CharField(max_length=100, blank=True, default="")
    mobile = models.CharField(max_length=15)
    is_new_user = models.BooleanField(default=False)
    logged_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.mobile} - {self.logged_at} - new={self.is_new_user}"
    
    def get_user_name(self):
        try:
            return self.user.profile.name if self.user.profile.name else self.mobile
        except:
            return self.mobile
    
    class Meta:
        verbose_name = "Login History"
        verbose_name_plural = "Login History"


# USER PROFILE - Stores user's health and diet information
class UserProfile(models.Model):
    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Others", "Others"),
    ]

    GOAL_CHOICES = [
        ("Weight Loss", "Weight Loss"),
        ("Weight Gain", "Weight Gain"),
        ("Muscle Gain", "Muscle Gain"),
    ]

    DIET_CHOICES = [
        ("Veg", "Veg"),
        ("Non-Veg", "Non-Veg"),
        ("Vegan", "Vegan"),
        ("Eggetarian", "Eggetarian"),
        ("Keto / Low-Carb", "Keto / Low-Carb"),
        ("High Protein", "High Protein"),
    ]

    WEIGHT_UNITS = [
        ("kg", "kg"),
        ("lbs", "lbs"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    weight_unit = models.CharField(max_length=5, choices=WEIGHT_UNITS, default="kg")
    height_cm = models.FloatField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    goal = models.CharField(max_length=50, choices=GOAL_CHOICES, null=True, blank=True)
    diet_preference = models.CharField(max_length=50, choices=DIET_CHOICES, null=True, blank=True)
    target_weight = models.FloatField(null=True, blank=True)
    health_conditions = models.JSONField(default=list, blank=True)
    other_condition_text = models.TextField(blank=True)
    allergies = models.JSONField(default=list, blank=True)
    allergy_notes = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to="profile_images/", null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user.mobile}"
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


# DAILY NUTRITION SUMMARY
class DailyNutritionSummary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="daily_summaries")
    user_name = models.CharField(max_length=100, blank=True, default="")
    date = models.DateField()
    calories_target = models.IntegerField(default=0)
    calories_consumed = models.IntegerField(default=0)
    protein_g = models.FloatField(default=0)
    protein_target = models.FloatField(default=0)
    carbs_g = models.FloatField(default=0)
    carbs_target = models.FloatField(default=0)
    fats_g = models.FloatField(default=0)
    fats_target = models.FloatField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Daily Nutrition Summary"
        verbose_name_plural = "Daily Nutrition Summaries"
        unique_together = ("user", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.user.mobile} - {self.date}"
    
    def get_user_name(self):
        try:
            return self.user.profile.name if self.user.profile.name else self.user.mobile
        except:
            return self.user.mobile

    @property
    def calories_remaining(self):
        return max(self.calories_target - self.calories_consumed, 0)


# MEAL ENTRY - Cleaned up to use name properly
class MealEntry(models.Model):
    MEAL_TYPES = [
        ("Breakfast", "Breakfast"),
        ("Brunch", "Brunch"),
        ("Lunch", "Lunch"),
        ("Evening Snacks", "Evening Snacks"),
        ("Dinner", "Dinner"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_name = models.CharField(max_length=100, blank=True, default="")
    date = models.DateField()
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES)
    name = models.CharField(max_length=200, default="Unknown food")
    serving = models.CharField(max_length=100, blank=True, default="")
    quantity = models.FloatField(default=1)
    calories = models.FloatField(default=0)
    protein_g = models.FloatField(default=0)
    carbs_g = models.FloatField(default=0)
    fats_g = models.FloatField(default=0)
    eaten = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_user_name(self):
        try:
            return self.user.profile.name if self.user.profile.name else self.user.mobile
        except:
            return self.user.mobile
    
    class Meta:
        verbose_name = "Meal Entry"
        verbose_name_plural = "Meal Entries"


# USER APP SETTINGS
class UserAppSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_name = models.CharField(max_length=100, blank=True, default="")
    notifications_enabled = models.BooleanField(default=True)
    meal_reminders_enabled = models.BooleanField(default=True)
    reminder_time = models.TimeField(null=True, blank=True)
    weekly_summary_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings for {self.user.mobile}"
    
    def get_user_name(self):
        try:
            return self.user.profile.name if self.user.profile.name else self.user.mobile
        except:
            return self.user.mobile


# MEAL RECOMMENDATION CACHE
class MealRecommendation(models.Model):
    MEAL_TYPES = [
        ("Breakfast", "Breakfast"),
        ("Brunch", "Brunch"),
        ("Lunch", "Lunch"),
        ("Evening Snacks", "Evening Snacks"),
        ("Dinner", "Dinner"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="meal_recommendations")
    user_name = models.CharField(max_length=100, blank=True, default="")
    date = models.DateField()
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES)
    items_json = models.JSONField(default=list, blank=True)
    goal = models.CharField(max_length=50, blank=True)
    diet_preference = models.CharField(max_length=50, blank=True)
    health_conditions = models.JSONField(default=list, blank=True)
    target_calories = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ("user", "date", "meal_type")
        ordering = ["-date"]
        verbose_name = "Daily Recommendation"
        verbose_name_plural = "Daily Recommendations"
    
    def __str__(self):
        return f"{self.user.mobile} - {self.date} - {self.meal_type}"
    
    def is_valid(self):
        expiry_date = self.created_at + timedelta(days=7)
        return timezone.now() < expiry_date
    
    def get_user_name(self):
        try:
            return self.user.profile.name if self.user.profile.name else self.user.mobile
        except:
            return self.user.mobile


# WEEKLY MEAL RECOMMENDATION
class WeeklyMealRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="weekly_recommendations")
    user_name = models.CharField(max_length=100, blank=True, default="")
    week_start_date = models.DateField()
    recommendations_data = models.JSONField(default=dict) # Store all meals for the week
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Weekly Recommendations"
        ordering = ["-week_start_date"]

    def __str__(self):
        return f"{self.user.mobile} - Week of {self.week_start_date}"
    
    def get_user_name(self):
        try:
            return self.user.profile.name if self.user.profile.name else self.user.mobile
        except:
            return self.user.mobile
