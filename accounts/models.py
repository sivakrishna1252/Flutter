from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from datetime import timedelta




# USER MANAGER - Custom manager for creating users and superusers
# Handles user creation logic with mobile number as username
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
# Uses mobile number instead of username for login
# Tracks onboarding completion status
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


# OTP MODEL - Stores one-time passwords for mobile verification
# Used during login/signup process
# Tracks if OTP is used and when it was created
class OTP(models.Model):
    mobile = models.CharField(max_length=15)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
   
        return False

    def __str__(self):
        return f"{self.mobile} - {self.code}"



# LOGIN HISTORY - Tracks all user login attempts
# Records if user was new during that login
# Useful for analytics and security monitoring
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




# USER PROFILE - Stores user's health and diet information
# Collected during onboarding process
# Includes: name, age, weight, height, gender, goals, diet preferences
# Also stores profile image and health conditions
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
    weight_unit = models.CharField(
        max_length=5,
        choices=WEIGHT_UNITS,
        default="kg",
    )

    height_cm = models.FloatField(null=True, blank=True)

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        null=True,
        blank=True,
    )

    goal = models.CharField(
        max_length=50,
        choices=GOAL_CHOICES,
        null=True,
        blank=True,
    )

    diet_preference = models.CharField(
        max_length=50,
        choices=DIET_CHOICES,
        null=True,
        blank=True,
    )

   
    health_conditions = models.JSONField(default=list, blank=True)
    other_condition_text = models.TextField(blank=True)

    allergies = models.JSONField(default=list, blank=True)
    allergy_notes = models.TextField(blank=True)

    profile_image = models.ImageField(
        upload_to="profile_images/",
        null=True,
        blank=True,
    )

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user.mobile}"

        

# DAILY NUTRITION SUMMARY - Per-user, per-day nutrition tracking
# Stores daily calorie targets and consumed amounts
# Tracks macros: protein, carbs, fats in grams
# Used for dashboard today/weekly/monthly views
class DailyNutritionSummary(models.Model):
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="daily_summaries")
    user_name = models.CharField(max_length=100, blank=True, default="")
    date = models.DateField()

    # calories
    calories_target = models.IntegerField(default=0)
    calories_consumed = models.IntegerField(default=0)

    # macros in grams
    protein_g = models.FloatField(default=0)
    protein_target = models.FloatField(default=0)
    
    carbs_g = models.FloatField(default=0)
    carbs_target = models.FloatField(default=0)
    
    fats_g = models.FloatField(default=0)
    fats_target = models.FloatField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
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

    def macro_percentages(self):
       
        protein_kcal = self.protein_g * 4
        carbs_kcal = self.carbs_g * 4
        fats_kcal = self.fats_g * 9

        total_kcal = protein_kcal + carbs_kcal + fats_kcal
        if total_kcal == 0:
            return {"protein_pct": 0, "carbs_pct": 0, "fats_pct": 0}

        return {
            "protein_pct": round(protein_kcal * 100 / total_kcal, 1),
            "carbs_pct": round(carbs_kcal * 100 / total_kcal, 1),
            "fats_pct": round(fats_kcal * 100 / total_kcal, 1),
        }


# FOOD DATABASE - Master list of food items
# Stores nutritional information per serving
# Includes: calories, protein, carbs, fats
# Can be filtered by diet type (Veg, Non-Veg, Vegan, etc.)
class Food(models.Model):
    name = models.CharField(max_length=255)
    serving = models.CharField(max_length=100, blank=True)

    calories = models.FloatField(default=0)
    protein_g = models.FloatField(default=0)
    carbs_g = models.FloatField(default=0)
    fats_g = models.FloatField(default=0)

    diet_type = models.CharField(
        max_length=50,
        choices=UserProfile.DIET_CHOICES,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name


# MEAL ENTRY - User's actual meal logs
# Records what user ate for each meal (Breakfast, Lunch, Dinner, etc.)
# Stores: food name, serving size, quantity, calculated macros
# Links to Food table (optional) and User
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

    food = models.ForeignKey(Food, on_delete=models.SET_NULL, null=True, blank=True)
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


# USER APP SETTINGS - App-level preferences for each user
# Controls notifications, meal reminders, weekly summaries
# Stores reminder time preferences
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


# MEAL RECOMMENDATION CACHE - Caches AI-generated meal recommendations
# Stores recommendations for 7 days to avoid repeated API calls
# Each recommendation includes items with images and nutritional data
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
    
    # Date for which recommendation is generated
    date = models.DateField()
    # Meal type for this recommendation
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES)
    
    # Cached recommendation data in JSON format
    # Contains: items (with name, serving, calories, protein_g, carbs_g, fats_g, note, image_url)
    items_json = models.JSONField(default=list, blank=True)
    
    # User profile data at time of recommendation
    goal = models.CharField(max_length=50, blank=True)
    diet_preference = models.CharField(max_length=50, blank=True)
    health_conditions = models.JSONField(default=list, blank=True)
    
    # For future use - daily target calories can be calculated from profile
    target_calories = models.IntegerField(null=True, blank=True)
    
    # Timestamp for cache validity
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ("user", "date", "meal_type")
        ordering = ["-date"]
    
    def __str__(self):
        return f"{self.user.mobile} - {self.date} - {self.meal_type}"
    
    def is_valid(self):
        """Check if recommendation is within 7-day cache period"""
        expiry_date = self.created_at + timedelta(days=7)
        return timezone.now() < expiry_date
    
    def get_user_name(self):
        try:
            return self.user.profile.name if self.user.profile.name else self.user.mobile
        except:
            return self.user.mobile
