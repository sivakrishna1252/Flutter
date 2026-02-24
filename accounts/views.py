import random
from datetime import datetime, timedelta, date
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from .models import (
    OTP,
    LoginHistory,
    UserProfile,
    UserAppSettings,
    DailyNutritionSummary,
    MealEntry,
    MealRecommendation,
    WeeklyMealRecommendation
)
from .ai_recommender import recommend_meals_for_user

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from .serializers import (
    SendOTPSerializer, VerifyOTPSerializer, OnboardingSerializer, 
    UserProfileSerializer, MealEntrySerializer, AddMealEntrySerializer,
    DailyNutritionSummarySerializer, UserAppSettingsSerializer
)

User = get_user_model()


# Helper function to calculate daily nutrition targets based on user profile
def calculate_nutrition_targets(user):
    """
    Calculate daily nutrition targets based on user profile data.
    Uses Mifflin-St Jeor formula for BMR and activity level adjustments.
    Accounts for diet preference, allergies, and health conditions.
    """
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        return {
            "calories_target": 2000,
            "protein_target": 150,
            "carbs_target": 200,
            "fats_target": 65
        }
    
    # Get profile data
    age = profile.age or 30
    weight_kg = profile.weight if profile.weight_unit == "kg" else (profile.weight / 2.205 if profile.weight else 70)
    height_cm = profile.height_cm or 170
    gender = profile.gender or "Male"
    diet_preference = profile.diet_preference or "Non-Veg"
    health_conditions = profile.health_conditions or []
    allergies = profile.allergies or []
    
    # Mifflin-St Jeor BMR formula
    if gender == "Male":
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
    
    # Activity level multiplier (Default to 1.55 as activity_level removed)
    multiplier = 1.55
    
    tdee = bmr * multiplier
    
    # Calories target = TDEE (no goal-based adjustment)
    calories_target = int(tdee)
    
    # Adjust macros based on health conditions
    protein_multiplier = 1.0
    
    if "Diabetes" in health_conditions:
        # Lower carbs for diabetes
        protein_multiplier = 1.1  # Slightly higher protein
    elif "High Blood Pressure" in health_conditions:
        protein_multiplier = 0.95  # Slightly lower protein
    elif "Thyroid Issues" in health_conditions:
        protein_multiplier = 1.05  # Balanced protein
    
    # Base macro calculations
    # Protein: 1.6g per kg body weight (adjusted by health conditions)
    protein_target = weight_kg * 1.6 * protein_multiplier
    
    # Fats: 0.9g per kg body weight
    fats_target = weight_kg * 0.9
    
    # Carbs: remaining calories
    carbs_kcal = max(calories_target - (protein_target * 4) - (fats_target * 9), 0)
    carbs_target = carbs_kcal / 4
    
    # Adjust for diet preference
    if diet_preference == "High Protein":
        protein_target = protein_target * 1.25
        carbs_target = max(carbs_target * 0.85, 0)
    elif diet_preference == "Keto / Low-Carb":
        carbs_target = carbs_target * 0.5
        fats_target = fats_target * 1.2
    elif diet_preference == "Vegan":
        # Vegan needs more total protein from plant sources
        protein_target = protein_target * 1.15
    
    return {
        "calories_target": calories_target,
        "protein_target": round(protein_target, 1),
        "carbs_target": round(carbs_target, 1),
        "fats_target": round(fats_target, 1),
        "diet_preference": diet_preference,
        "health_conditions": health_conditions,
        "allergies": allergies
    }


#send-otp (checking purpose)
class SendOTPView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=SendOTPSerializer,
        responses={200: OpenApiTypes.OBJECT},
        description="Send OTP to mobile number"
    )
    def post(self, request):
        mobile = request.data.get('mobile')

        if not mobile:
            return Response(
                {"error": "Mobile is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # OTP generate (random 6 digits)
        otp_code = f"{random.randint(100000, 999999)}"
        # we want fixed otp use this one : otp_code = "123456"

        OTP.objects.update_or_create(
            mobile=mobile,
            is_used=False,
            defaults={"code": otp_code}
        )

        print(f"[DEV] OTP for {mobile} = {otp_code}")

        return Response(
            {
                "message": "OTP generated successfully (TEST MODE)",
                "otp": otp_code   
            },
            status=status.HTTP_200_OK
        )


#Verify-OTP
class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=VerifyOTPSerializer,
        responses={200: OpenApiTypes.OBJECT},
        description="Verify OTP and login/register user"
    )
    def post(self, request):
        mobile = request.data.get('mobile')
        code = request.data.get('otp')

        if not mobile or not code:
            return Response(
                {"error": "Mobile and OTP are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            otp_obj = OTP.objects.filter(
                mobile=mobile,
                code=code,
                is_used=False
            ).latest('created_at')
        except OTP.DoesNotExist:
            return Response(
                {"error": "Invalid OTP"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if otp_obj.is_expired():
            return Response(
                {"error": "OTP expired"},
                status=status.HTTP_400_BAD_REQUEST
            )

        otp_obj.is_used = True
        otp_obj.save()

        user, created = User.objects.get_or_create(
            mobile=mobile
        )

        #Login-History
        user_name = ""
        try:
            user_name = user.profile.name if user.profile.name else ""
        except:
            pass
        
        LoginHistory.objects.create(
            user=user,
            user_name=user_name,
            mobile=user.mobile,
            is_new_user=created,
        )

        # Refresh Login History: Delete logs older than 7 days
        one_week_ago = timezone.now() - timedelta(days=7)
        LoginHistory.objects.filter(logged_at__lt=one_week_ago).delete()

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return Response(
            {
                "access": str(access),
                "refresh": str(refresh),
                "is_new_user": created,
                "onboarding_completed": user.onboarding_completed,
            },
            status=status.HTTP_200_OK
        )


#perosn details
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        description="Get current user details"
    )
    def get(self, request):
        user = request.user
        return Response(
            {
                "id": user.id,
                "mobile": user.mobile,
                "onboarding_completed": user.onboarding_completed,
            },
            status=status.HTTP_200_OK
        )


#Logout
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        description="Logout user and blacklist tokens"
    )
    def post(self, request):
        try:
            tokens = OutstandingToken.objects.filter(user=request.user)
            for token in tokens:
                BlacklistedToken.objects.get_or_create(token=token)
        except Exception as e:
            print("Logout error:", e)

        return Response(
            {"message": "Logged out successfully"},
            status=status.HTTP_200_OK
        )


#Onboarding Options
class OnboardingOptionsView(APIView):
    permission_classes = [AllowAny] #[IsAuthenticated]

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        description="Get available options for onboarding (goals, diets, conditions)"
    )
    def get(self, request):
        options = {
            "goals": ["Weight Loss", "Weight Gain", "Muscle Gain"],
            "diet_preferences": [
                "Veg",
                "Non-Veg",
                "Vegan",
                "Eggetarian",
                "Keto / Low-Carb",
                "High Protein",
            ],
            "health_conditions": [
                "Diabetes",
                "Hypertension",
                "Thyroid",
                "PCOS / PCOD",
                "Digestive Issues",
                "Food Allergies",
                "Others",
                "None of These",
            ],
            "allergies": [
                "Peanuts",
                "Tree Nuts",
                "Milk/Dairy",
                "Eggs",
                "Fish",
                "Shellfish",
                "Soy",
                "Wheat/Gluten",
                "Sesame",
                "Mustard",
                "Others",
                "None of These",
            ],
        }
        return Response(options, status=status.HTTP_200_OK)

#onboarding complete
class OnboardingCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=OnboardingSerializer,
        responses={200: OpenApiTypes.OBJECT},
        description="Save user onboarding profile data"
    )
    def post(self, request):
        user = request.user
        data = request.data

        name = data.get("name")
        age = data.get("age")
        weight = data.get("weight")
        weight_unit = data.get("weight_unit", "kg")
        height_cm = data.get("height_cm")
        gender = data.get("gender")
        goal = data.get("goal")
        diet_preference = data.get("diet_preference",[])
        health_conditions = data.get("health_conditions", [])
        other_condition_text = data.get("other_condition_text", "")
        allergies = data.get("allergies", [])
        allergy_notes = data.get("allergy_notes", "")
        target_weight = data.get("target_weight")

        # simple validations
        if not name:
            return Response({"error": "name is required"}, status=400)
        if not weight:
            return Response({"error": "weight is required"}, status=400)
        if not height_cm:
            return Response({"error": "height_cm is required"}, status=400)
        if not goal:
            return Response({"error": "goal is required"}, status=400)
        if not diet_preference:
            return Response({"error": "diet_preference is required"}, status=400)

        if health_conditions is None:
            health_conditions = []
        
        if not isinstance(health_conditions, list):
            return Response({"error": "health_conditions m  ust be a list"}, status=400)
        
        if allergies is None:
            allergies = []
        
        if not isinstance(allergies, list):
            return Response({"error": "allergies must be a list"}, status=400)


# create or update profile
        profile, created = UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "name": name,
                "age": age,
                "weight": weight,
                "weight_unit": weight_unit,
                "height_cm": height_cm,
                "gender": gender,
                "goal": goal,
                "diet_preference": diet_preference,
                "health_conditions": health_conditions,
                "other_condition_text": other_condition_text,
                "allergies": allergies,
                "allergy_notes": allergy_notes,
                "target_weight": target_weight,
            },
        )

        # Update user_name in related tables
        DailyNutritionSummary.objects.filter(user=user).update(user_name=name)
        MealEntry.objects.filter(user=user).update(user_name=name)
        UserAppSettings.objects.filter(user=user).update(user_name=name)
        LoginHistory.objects.filter(user=user).update(user_name=name)

        user.onboarding_completed = True
        user.save(update_fields=["onboarding_completed"])

        return Response(
            {
                "message": "Onboarding saved successfully",
                "onboarding_completed": True,
            },
            status=status.HTTP_200_OK,
        )


#onboarding profile
class OnboardingProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        description="Get user's onboarding profile data"
    )
    def get(self, request):
        user = request.user
        try:
            profile = user.profile  
        except UserProfile.DoesNotExist:
          
            return Response(
                {
                    "name": "",
                    "age": None,
                    "weight": None,
                    "weight_unit": "kg",
                    "height_cm": None,
                    "gender": None,
                    "goal": None,
                    "diet_preference": None,
                    "health_conditions": [],
                    "other_condition_text": "",
                    "onboarding_completed": user.onboarding_completed,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "name": profile.name,
                "age": profile.age,
                "weight": profile.weight,
                "weight_unit": profile.weight_unit,
                "height_cm": profile.height_cm,
                "gender": profile.gender,
                "goal": profile.goal,
                "diet_preference": profile.diet_preference,
                "target_weight": profile.target_weight,
                "health_conditions": profile.health_conditions,
                "other_condition_text": profile.other_condition_text,
                "allergies": profile.allergies,
                "allergy_notes": profile.allergy_notes,
                "onboarding_completed": user.onboarding_completed,
            },
            status=status.HTTP_200_OK,
        )


#dashboard/today
class DashboardTodayView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        description="Get today's nutrition summary (calories, macros)"
    )
    def get(self, request):
        user = request.user
        today = timezone.localdate()

        # Get user's name
        user_name = "User"
        try:
            user_name = user.profile.name if user.profile.name else "User"
        except:
            pass

        # Get nutrition targets based on user profile
        targets = calculate_nutrition_targets(user)

        # Calculate total consumed from all eaten meals for today
        eaten_meals = MealEntry.objects.filter(user=user, date=today, eaten=True)
        total_consumed = {
            "calories": sum(meal.calories for meal in eaten_meals),
            "protein_g": sum(meal.protein_g for meal in eaten_meals),
            "carbs_g": sum(meal.carbs_g for meal in eaten_meals),
            "fats_g": sum(meal.fats_g for meal in eaten_meals),
        }

        summary, created = DailyNutritionSummary.objects.get_or_create(
            user=user,
            date=today,
            defaults={
                "user_name": user_name,
                "calories_target": targets["calories_target"],
                "protein_target": targets["protein_target"],
                "carbs_target": targets["carbs_target"],
                "fats_target": targets["fats_target"],
                "calories_consumed": total_consumed["calories"],
                "protein_g": total_consumed["protein_g"],
                "carbs_g": total_consumed["carbs_g"],
                "fats_g": total_consumed["fats_g"],
            },
        )

        # Always refresh consumed totals and sync targets from profile
        summary.calories_consumed = total_consumed["calories"]
        summary.protein_g = total_consumed["protein_g"]
        summary.carbs_g = total_consumed["carbs_g"]
        summary.fats_g = total_consumed["fats_g"]
        
        # Keep targets in sync with profile
        summary.calories_target = targets["calories_target"]
        summary.protein_target = targets["protein_target"]
        summary.carbs_target = targets["carbs_target"]
        summary.fats_target = targets["fats_target"]
        
        summary.save()
        
        if not summary.user_name:
            summary.user_name = user_name
            summary.save()

        def get_pct(consumed, target):
            if not target or target <= 0: return 0
            return min(round((consumed / target) * 100), 100)

        data = {
            "user_name": user_name,
            "date": today.isoformat(),
            "calories": {
                "consumed": int(summary.calories_consumed),
                "target": int(summary.calories_target),
                "remaining": max(int(summary.calories_target - summary.calories_consumed), 0),
                "percentage": get_pct(summary.calories_consumed, summary.calories_target)
            },
            "proteins": {
                "consumed": round(summary.protein_g, 1),
                "target": round(summary.protein_target, 1),
                "remaining": round(max(summary.protein_target - summary.protein_g, 0), 1),
                "percentage": get_pct(summary.protein_g, summary.protein_target)
            },
            "carbs": {
                "consumed": round(summary.carbs_g, 1),
                "target": round(summary.carbs_target, 1),
                "remaining": round(max(summary.carbs_target - summary.carbs_g, 0), 1),
                "percentage": get_pct(summary.carbs_g, summary.carbs_target)
            },
            "fats": {
                "consumed": round(summary.fats_g, 1),
                "target": round(summary.fats_target, 1),
                "remaining": round(max(summary.fats_target - summary.fats_g, 0), 1),
                "percentage": get_pct(summary.fats_g, summary.fats_target)
            }
        }
        return Response(data, status=status.HTTP_200_OK)

#dashboard/weekly
class DashboardWeeklyView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        description="Get nutrition summary for the last 7 days"
    )
    def get(self, request):
        user = request.user
        today = timezone.localdate()
        start_date = today - timedelta(days=6)

        user_name = "User"
        try:
            user_name = user.profile.name if user.profile.name else "User"
        except:
            pass

        qs = DailyNutritionSummary.objects.filter(
            user=user, date__gte=start_date, date__lte=today
        ).order_by("date")

        by_date = {obj.date: obj for obj in qs}

        days = []
        total_target_cal = 0
        total_consumed_cal = 0
        total_target_protein = 0
        total_consumed_protein = 0
        total_target_carbs = 0
        total_consumed_carbs = 0
        total_target_fats = 0
        total_consumed_fats = 0

        # Get current daily targets from profile for missing days
        current_targets = calculate_nutrition_targets(user)

        for i in range(7):
            d = start_date + timedelta(days=i)
            obj = by_date.get(d)
            if obj:
                days.append({
                    "date": d.isoformat(),
                    "calories": int(obj.calories_consumed),
                    "calories_target": int(obj.calories_target),
                    "proteins": round(obj.protein_g, 1),
                    "proteins_target": round(obj.protein_target, 1),
                    "carbs": round(obj.carbs_g, 1),
                    "carbs_target": round(obj.carbs_target, 1),
                    "fats": round(obj.fats_g, 1),
                    "fats_target": round(obj.fats_target, 1),
                })
                total_target_cal += obj.calories_target
                total_consumed_cal += obj.calories_consumed
                total_target_protein += obj.protein_target
                total_consumed_protein += obj.protein_g
                total_target_carbs += obj.carbs_target
                total_consumed_carbs += obj.carbs_g
                total_target_fats += obj.fats_target
                total_consumed_fats += obj.fats_g
            else:
                days.append({
                    "date": d.isoformat(),
                    "calories": 0,
                    "calories_target": int(current_targets["calories_target"]),
                    "proteins": 0.0,
                    "proteins_target": round(current_targets["protein_target"], 1),
                    "carbs": 0.0,
                    "carbs_target": round(current_targets["carbs_target"], 1),
                    "fats": 0.0,
                    "fats_target": round(current_targets["fats_target"], 1),
                })
                total_target_cal += current_targets["calories_target"]
                total_target_protein += current_targets["protein_target"]
                total_target_carbs += current_targets["carbs_target"]
                total_target_fats += current_targets["fats_target"]

        def get_pct(consumed, target):
            if not target or target <= 0: return 0
            return min(round((consumed / target) * 100), 100)

        data = {
            "user_name": user_name,
            "start_date": start_date.isoformat(),
            "end_date": today.isoformat(),
            "calories": {
                "consumed": int(total_consumed_cal),
                "target": int(total_target_cal),
                "remaining": max(int(total_target_cal - total_consumed_cal), 0),
                "percentage": get_pct(total_consumed_cal, total_target_cal)
            },
            "proteins": {
                "consumed": round(total_consumed_protein, 1),
                "target": round(total_target_protein, 1),
                "remaining": round(max(total_target_protein - total_consumed_protein, 0), 1),
                "percentage": get_pct(total_consumed_protein, total_target_protein)
            },
            "carbs": {
                "consumed": round(total_consumed_carbs, 1),
                "target": round(total_target_carbs, 1),
                "remaining": round(max(total_target_carbs - total_consumed_carbs, 0), 1),
                "percentage": get_pct(total_consumed_carbs, total_target_carbs)
            },
            "fats": {
                "consumed": round(total_consumed_fats, 1),
                "target": round(total_target_fats, 1),
                "remaining": round(max(total_target_fats - total_consumed_fats, 0), 1),
                "percentage": get_pct(total_consumed_fats, total_target_fats)
            },
            "days": days
        }
        return Response(data, status=status.HTTP_200_OK)

#dashboard/monthly
class DashboardMonthlyView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='month',
                description='Month in YYYY-MM format (optional, defaults to current month)',
                required=False,
                type=OpenApiTypes.STR,
            ),
        ],
        responses={200: OpenApiTypes.OBJECT},
        description="Get nutrition summary for a specific month"
    )
    def get(self, request):
        user = request.user
        month_str = request.query_params.get("month")

        user_name = "User"
        try:
            user_name = user.profile.name if user.profile.name else "User"
        except:
            pass
       
        if month_str:
            try:
                year, month = map(int, month_str.split("-"))
                first_day = date(year, month, 1)
            except Exception:
                return Response({"error": "Invalid month format. Use YYYY-MM"},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            today = timezone.localdate()
            first_day = date(today.year, today.month, 1)

        if first_day.month == 12:
            next_month = date(first_day.year + 1, 1, 1)
        else:
            next_month = date(first_day.year, first_day.month + 1, 1)
        last_day = next_month - timedelta(days=1)

        qs = DailyNutritionSummary.objects.filter(
            user=user, date__gte=first_day, date__lte=last_day
        ).order_by("date")

        by_date = {obj.date: obj for obj in qs}
        
        days = []
        total_target_cal = 0
        total_consumed_cal = 0
        total_target_protein = 0
        total_consumed_protein = 0
        total_target_carbs = 0
        total_consumed_carbs = 0
        total_target_fats = 0
        total_consumed_fats = 0

        current_targets = calculate_nutrition_targets(user)
        d = first_day
        while d <= last_day:
            obj = by_date.get(d)
            if obj:
                days.append({
                    "date": d.isoformat(),
                    "calories": int(obj.calories_consumed),
                    "calories_target": int(obj.calories_target),
                    "proteins": round(obj.protein_g, 1),
                    "proteins_target": round(obj.protein_target, 1),
                    "carbs": round(obj.carbs_g, 1),
                    "carbs_target": round(obj.carbs_target, 1),
                    "fats": round(obj.fats_g, 1),
                    "fats_target": round(obj.fats_target, 1),
                })
                total_target_cal += obj.calories_target
                total_consumed_cal += obj.calories_consumed
                total_target_protein += obj.protein_target
                total_consumed_protein += obj.protein_g
                total_target_carbs += obj.carbs_target
                total_consumed_carbs += obj.carbs_g
                total_target_fats += obj.fats_target
                total_consumed_fats += obj.fats_g
            else:
                days.append({
                    "date": d.isoformat(),
                    "calories": 0,
                    "calories_target": int(current_targets["calories_target"]),
                    "proteins": 0.0,
                    "proteins_target": round(current_targets["protein_target"], 1),
                    "carbs": 0.0,
                    "carbs_target": round(current_targets["carbs_target"], 1),
                    "fats": 0.0,
                    "fats_target": round(current_targets["fats_target"], 1),
                })
                total_target_cal += current_targets["calories_target"]
                total_target_protein += current_targets["protein_target"]
                total_target_carbs += current_targets["carbs_target"]
                total_target_fats += current_targets["fats_target"]
            d += timedelta(days=1)

        def get_pct(consumed, target):
            if not target or target <= 0: return 0
            return min(round((consumed / target) * 100), 100)

        data = {
            "user_name": user_name,
            "month": first_day.strftime("%Y-%m"),
            "start_date": first_day.isoformat(),
            "end_date": last_day.isoformat(),
            "calories": {
                "consumed": int(total_consumed_cal),
                "target": int(total_target_cal),
                "remaining": max(int(total_target_cal - total_consumed_cal), 0),
                "percentage": get_pct(total_consumed_cal, total_target_cal)
            },
            "proteins": {
                "consumed": round(total_consumed_protein, 1),
                "target": round(total_target_protein, 1),
                "remaining": round(max(total_target_protein - total_consumed_protein, 0), 1),
                "percentage": get_pct(total_consumed_protein, total_target_protein)
            },
            "carbs": {
                "consumed": round(total_consumed_carbs, 1),
                "target": round(total_target_carbs, 1),
                "remaining": round(max(total_target_carbs - total_consumed_carbs, 0), 1),
                "percentage": get_pct(total_consumed_carbs, total_target_carbs)
            },
            "fats": {
                "consumed": round(total_consumed_fats, 1),
                "target": round(total_target_fats, 1),
                "remaining": round(max(total_target_fats - total_consumed_fats, 0), 1),
                "percentage": get_pct(total_consumed_fats, total_target_fats)
            },
            "days": days,
        }
        return Response(data, status=status.HTTP_200_OK)
class MealCategoriesView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        description="Get list of available meal categories"
    )
    def get(self, request):
        categories = [mt[0] for mt in MealEntry.MEAL_TYPES]
        return Response({"categories": categories}, status=status.HTTP_200_OK)


#--meals-categories--

class MealCategoriesView(APIView):
    permission_classes = [AllowAny] 

    def get(self, request):
        categories = [mt[0] for mt in MealEntry.MEAL_TYPES]
        return Response(
            {"categories": categories},
            status=status.HTTP_200_OK
        )



class MealRecommendationsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='date',
                description='Date in YYYY-MM-DD format (optional, defaults to today)',
                required=False,
                type=OpenApiTypes.DATE,
            ),
        ],
    )
    def get(self, request):
        """
        Get meal recommendations for a specific date.
        Returns ALL meal types (breakfast, brunch, lunch, evening snacks, dinner) for that date.
        Stores recommendations in database and returns cached data on subsequent requests.
        """
        user = request.user
        date_str = request.query_params.get("date")

        # Use today's date if not provided
        if not date_str:
            date_obj = datetime.now().date()
        else:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Load user profile
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "Onboarding not completed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # All meal types to generate recommendations for
        meal_types = ["Breakfast", "Brunch", "Lunch", "Evening Snacks", "Dinner"]
        all_recommendations = []

        # Process each meal type
        for meal_type in meal_types:
            try:
                # Check if recommendation exists in cache and is valid
                meal_rec = MealRecommendation.objects.get(
                    user=user,
                    date=date_obj,
                    meal_type=meal_type
                )
                
                if meal_rec.is_valid():
                    # Return cached recommendation
                    all_recommendations.append({
                        "meal_type": meal_type,
                        "goal": meal_rec.goal,
                        "diet_preference": meal_rec.diet_preference,
                        "health_conditions": meal_rec.health_conditions,
                        "target_calories": meal_rec.target_calories,
                        "items": meal_rec.items_json,
                        "cached": True,
                        "created_at": meal_rec.created_at.isoformat(),
                    })
                    print(f"✓ Retrieved cached recommendation for {user.mobile} - {date_obj} - {meal_type}")
                else:
                    # Cache expired, delete and regenerate
                    print(f"⟳ Cache expired for {meal_type}, regenerating...")
                    meal_rec.delete()
                    raise MealRecommendation.DoesNotExist
            except MealRecommendation.DoesNotExist:
                # Cache miss or expired - call AI to generate recommendations
                ai_response = recommend_meals_for_user(profile, meal_type)
                
                # Check for errors in AI response
                if "error" in ai_response:
                    print(f"✗ Error generating AI recommendation for {meal_type}: {ai_response['error']}")
                    all_recommendations.append({
                        "meal_type": meal_type,
                        "error": ai_response["error"],
                    })
                    continue
                
                items = ai_response.get("items", [])
                target_calories = self._calculate_target_calories(profile, meal_type)
                
                # Save recommendation to database
                try:
                    meal_rec = MealRecommendation.objects.create(
                        user=user,
                        user_name=profile.name,
                        date=date_obj,
                        meal_type=meal_type,
                        items_json=items,
                        goal=profile.goal,
                        diet_preference=profile.diet_preference,
                        health_conditions=profile.health_conditions or [],
                        target_calories=target_calories,
                    )
                    print(f"✓ Generated and cached recommendation for {user.mobile} - {date_obj} - {meal_type}")
                except Exception as e:
                    print(f"✗ Failed to cache recommendation: {str(e)}")
                
                all_recommendations.append({
                    "meal_type": meal_type,
                    "goal": profile.goal,
                    "diet_preference": profile.diet_preference,
                    "health_conditions": profile.health_conditions or [],
                    "target_calories": target_calories,
                    "items": items,
                    "cached": False,
                    "created_at": datetime.now().isoformat(),
                })

        return Response(
            {
                "date": date_obj.isoformat(),
                "user_name": profile.name,
                "recommendations": all_recommendations,
            },
            status=status.HTTP_200_OK,
        )

    def _calculate_target_calories(self, profile, meal_type):
        """
        Calculate target calories for a meal based on user profile and meal type.
        Basic formula: BMR * activity multiplier, then divide by meal count
        """
        try:
            weight = profile.weight or 70  # Default 70 kg
            height = profile.height_cm or 175  # Default 175 cm
            age = profile.age or 30  # Default 30 years
            gender = profile.gender or "Male"
            goal = profile.goal or "Weight Loss"
            
            # Harris-Benedict BMR calculation
            if gender == "Female":
                bmr = 655 + (9.6 * weight) + (1.8 * height) - (4.7 * age)
            else:
                bmr = 88 + (13.4 * weight) + (4.8 * height) - (5.7 * age)
            
            # Adjust based on goal
            if goal == "Weight Loss":
                tdee = bmr * 1.4  # Light activity
            elif goal == "Weight Gain":
                tdee = bmr * 1.6  # Moderate activity
            else:  # Muscle Gain
                tdee = bmr * 1.5  # Moderate activity
            
            # Meal type calorie percentages
            meal_percentages = {
                "Breakfast": 0.25,
                "Brunch": 0.15,
                "Lunch": 0.35,
                "Evening Snacks": 0.10,
                "Dinner": 0.30,
            }
            
            percentage = meal_percentages.get(meal_type, 0.25)
            target = int(tdee * percentage)
            return max(target, 300)  # Minimum 300 calories per meal
        except Exception as e:
            print(f"Error calculating target calories: {e}")
            return 500  # Default fallback


class WeeklyMealRecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='week_start_date',
                description='Start date of the week (YYYY-MM-DD). Defaults to the most recent Monday.',
                required=False,
                type=OpenApiTypes.DATE,
            ),
        ],
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request):
        user = request.user
        date_str = request.query_params.get("week_start_date")

        if not date_str:
            # Fallback to current Monday
            today = timezone.localdate()
            monday = today - timedelta(days=today.weekday())
        else:
            try:
                monday = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return Response({"error": "Invalid date format. Use YYYY-MM-DD"}, status=400)

        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            return Response({"error": "Onboarding not completed"}, status=400)

        # Check for cached weekly recommendation
        weekly_rec, created = WeeklyMealRecommendation.objects.get_or_create(
            user=user,
            week_start_date=monday,
            defaults={"user_name": profile.name}
        )

        if not weekly_rec.recommendations_data or created:
            # Generate recommendations for 7 days
            week_data = {}
            meal_types = ["Breakfast", "Brunch", "Lunch", "Evening Snacks", "Dinner"]
            
            for i in range(7):
                current_day = monday + timedelta(days=i)
                day_key = str(current_day)
                week_data[day_key] = {}
                
                for m_type in meal_types:
                    ai_resp = recommend_meals_for_user(profile, m_type)
                    week_data[day_key][m_type] = ai_resp.get("items", [])
            
            weekly_rec.recommendations_data = week_data
            weekly_rec.save()

        return Response({
            "user_name": profile.name,
            "week_start_date": monday.isoformat(),
            "recommendations": weekly_rec.recommendations_data
        }, status=status.HTTP_200_OK)


#Daywise meals
class DayMealsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='date',
                description='Date in YYYY-MM-DD format (required)',
                required=True,
                type=OpenApiTypes.DATE,
            ),
        ],
        responses={200: OpenApiTypes.OBJECT},
        description="Get all meals for a specific day grouped by meal type"
    )
    def get(self, request):
        user = request.user
        date_str = request.query_params.get("date")

        if not date_str:
            return Response(
                {"error": "date is required as YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Fetch all meal entries for that day, grouped by meal type
        entries = MealEntry.objects.filter(
            user=user,
            date=date_obj
        ).order_by("meal_type", "id")

        # Prepare empty structure with all standard meal types
        meal_map = {
            "Breakfast": [],
            "Brunch": [],
            "Lunch": [],
            "Evening Snacks": [],
            "Dinner": [],
        }

        # Initialize totals
        totals = {
            "calories": 0.0,
            "protein_g": 0.0,
            "carbs_g": 0.0,
            "fats_g": 0.0,
        }

        # Process each meal entry
        for entry in entries:
            meal_item = {
                "id": entry.id,
                "name": entry.name,
                "serving": entry.serving,
                "quantity": entry.quantity,
                "calories": float(entry.calories),
                "protein_g": float(entry.protein_g),
                "carbs_g": float(entry.carbs_g),
                "fats_g": float(entry.fats_g),
                "eaten": entry.eaten,
            }

            # Add meal to appropriate meal type list
            if entry.meal_type in meal_map:
                meal_map[entry.meal_type].append(meal_item)
            else:
                # Handle unexpected meal types
                if entry.meal_type not in meal_map:
                    meal_map[entry.meal_type] = []
                meal_map[entry.meal_type].append(meal_item)

            # Update totals
            totals["calories"] += float(entry.calories)
            totals["protein_g"] += float(entry.protein_g)
            totals["carbs_g"] += float(entry.carbs_g)
            totals["fats_g"] += float(entry.fats_g)

        # Round totals to 2 decimal places
        totals = {
            "calories": round(totals["calories"], 2),
            "protein_g": round(totals["protein_g"], 2),
            "carbs_g": round(totals["carbs_g"], 2),
            "fats_g": round(totals["fats_g"], 2),
        }

        return Response(
            {
                "date": date_obj.isoformat(),
                "meals": meal_map,
                "totals": totals,
            },
            status=status.HTTP_200_OK,
        )

#weekly macros
class WeeklyMacrosView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        description="Get weekly macro breakdown (protein, carbs, fats) for last 7 days"
    )
    def get(self, request):
        user = request.user

        today = timezone.localdate()
        from_date = today - timedelta(days=6)  # last 7 days (including today)

        summaries = DailyNutritionSummary.objects.filter(
            user=user,
            date__range=(from_date, today)
        ).order_by("date")

        # collect daily list for charts
        daily = []
        total_protein = total_carbs = total_fats = 0.0

        for s in summaries:
            daily.append({
                "date": s.date.isoformat(),
                "protein_g": s.protein_g,
                "carbs_g": s.carbs_g,
                "fats_g": s.fats_g,
            })
            total_protein += s.protein_g
            total_carbs += s.carbs_g
            total_fats += s.fats_g

        total_all = total_protein + total_carbs + total_fats
        if total_all > 0:
            protein_pct = (total_protein / total_all) * 100.0
            carbs_pct = (total_carbs / total_all) * 100.0
            fats_pct = (total_fats / total_all) * 100.0
        else:
            protein_pct = carbs_pct = fats_pct = 0.0

        return Response(
            {
                "from": from_date.isoformat(),
                "to": today.isoformat(),
                "totals": {
                    "protein_g": total_protein,
                    "carbs_g": total_carbs,
                    "fats_g": total_fats,
                    "protein_pct": round(protein_pct, 1),
                    "carbs_pct": round(carbs_pct, 1),
                    "fats_pct": round(fats_pct, 1),
                },
                "daily": daily,  
            },
            status=status.HTTP_200_OK,
        )

#calories trend
class CaloriesTrendView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='from',
                description='Start date in YYYY-MM-DD format (optional, defaults to 7 days ago)',
                required=False,
                type=OpenApiTypes.DATE,
            ),
            OpenApiParameter(
                name='to',
                description='End date in YYYY-MM-DD format (optional, defaults to today)',
                required=False,
                type=OpenApiTypes.DATE,
            ),
        ],
        responses={200: OpenApiTypes.OBJECT},
        description="Get calorie consumption trend for a date range"
    )
    def get(self, request):
        user = request.user
        from_str = request.query_params.get("from")
        to_str = request.query_params.get("to")

        # default last 7 days if not provided
        if not from_str or not to_str:
            today = timezone.localdate()
            from_date = today - timedelta(days=6)
            to_date = today
        else:
            try:
                from_date = datetime.strptime(from_str, "%Y-%m-%d").date()
                to_date = datetime.strptime(to_str, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"error": "from/to must be YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if from_date > to_date:
            return Response(
                {"error": "from date must be <= to date"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        summaries = DailyNutritionSummary.objects.filter(
            user=user,
            date__range=(from_date, to_date)
        ).order_by("date")

        series = []
        for s in summaries:
            series.append({
                "date": s.date.isoformat(),
                "calories_target": s.calories_target,
                "calories_consumed": s.calories_consumed,
                "calories_remaining": s.calories_remaining,
            })

        return Response(
            {
                "from": from_date.isoformat(),
                "to": to_date.isoformat(),
                "data": series,
            },
            status=status.HTTP_200_OK,
        )

#Add meals

class AddMealEntryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=AddMealEntrySerializer,
        responses=AddMealEntrySerializer
    )
    def post(self, request):
        user = request.user
        data = request.data

        date_str   = data.get("date")
        meal_type  = data.get("meal_type")
        name       = data.get("name")
        serving    = data.get("serving", "")

        calories   = data.get("calories")
        protein_g  = data.get("protein_g", 0)
        carbs_g    = data.get("carbs_g", 0)
        fats_g     = data.get("fats_g", 0)
        quantity   = data.get("quantity", 1)

      
        if not (date_str and meal_type and name and calories is not None):
            return Response(
                {"error": "date, meal_type, name, calories are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Invalid date format, use YYYY-MM-DD"}, status=400)

        # convert to float
        quantity   = float(quantity)
        calories   = float(calories)
        protein_g  = float(protein_g)
        carbs_g    = float(carbs_g)
        fats_g     = float(fats_g)

        # 1 serving macros
        one_cal   = calories
        one_prot  = protein_g
        one_carbs = carbs_g
        one_fats  = fats_g

        # same user + same date + same meal_type + same name unte → quantity increase

        user_name = "User"
        try:
            user_name = user.profile.name if user.profile.name else "User"
        except:
            pass

        entry, created = MealEntry.objects.get_or_create(
            user=user,
            date=date_obj,
            meal_type=meal_type,
            name=name,
            defaults={
                "user_name": user_name,
                "serving": serving,
                "quantity": quantity,
                "calories": one_cal * quantity,
                "protein_g": one_prot * quantity,
                "carbs_g": one_carbs * quantity,
                "fats_g": one_fats * quantity,
            },
        )

        if not created:
            entry.quantity += quantity
            entry.calories  += one_cal * quantity
            entry.protein_g += one_prot * quantity
            entry.carbs_g   += one_carbs * quantity
            entry.fats_g    += one_fats * quantity

            if not entry.serving:
                entry.serving = serving

        entry.save()

        # daily summary update
        summary, _ = DailyNutritionSummary.objects.get_or_create(
            user=user,
            date=date_obj,
            defaults={"calories_target": 0},
        )
        summary.calories_consumed += one_cal * quantity
        summary.protein_g         += one_prot * quantity
        summary.carbs_g           += one_carbs * quantity
        summary.fats_g            += one_fats * quantity
        summary.save()

        return Response(
            {
                "message": "meal saved",
                "entry": {
                    "id": entry.id,
                    "date": str(entry.date),
                    "meal_type": entry.meal_type,
                    "name": entry.name,
                    "serving": entry.serving,
                    "quantity": entry.quantity,
                    "calories": entry.calories,
                    "protein_g": entry.protein_g,
                    "carbs_g": entry.carbs_g,
                    "fats_g": entry.fats_g,
                },
            },
            status=status.HTTP_200_OK,
        )

#Remove meal
class RemoveMealEntryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='entry_id',
                description='ID of the meal entry to remove',
                required=True,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
            ),
        ],
        responses={200: OpenApiTypes.OBJECT},
        description="Delete or decrement quantity of a meal entry"
    )
    def delete(self, request, entry_id):
        user = request.user

        try:
            entry = MealEntry.objects.get(id=entry_id, user=user)
        except MealEntry.DoesNotExist:
            return Response({"error": "Entry not found"}, status=404)

        date_obj = entry.date

        if entry.quantity <= 0:
            # safety guard
            entry.delete()
            return Response({"message": "Entry removed"}, status=200)

        # macros per 1 serving (before decrement)
        one_cal   = entry.calories  / entry.quantity
        one_prot  = entry.protein_g / entry.quantity
        one_carbs = entry.carbs_g   / entry.quantity
        one_fats  = entry.fats_g    / entry.quantity

        summary, _ = DailyNutritionSummary.objects.get_or_create(
            user=user,
            date=date_obj,
            defaults={"calories_target": 0},
        )

        if entry.quantity > 1:
            entry.quantity -= 1
            entry.calories  -= one_cal
            entry.protein_g -= one_prot
            entry.carbs_g   -= one_carbs
            entry.fats_g    -= one_fats
            entry.save()

            summary.calories_consumed -= one_cal
            summary.protein_g         -= one_prot
            summary.carbs_g           -= one_carbs
            summary.fats_g            -= one_fats
            summary.save()

            return Response(
                {
                    "message": "one serving removed",
                    "entry": {
                        "id": entry.id,
                        "quantity": entry.quantity,
                        "calories": entry.calories,
                        "protein_g": entry.protein_g,
                        "carbs_g": entry.carbs_g,
                        "fats_g": entry.fats_g,
                    },
                },
                status=200,
            )

        # quantity == 1 → delete row
        summary.calories_consumed -= entry.calories
        summary.protein_g         -= entry.protein_g
        summary.carbs_g           -= entry.carbs_g
        summary.fats_g            -= entry.fats_g
        summary.save()

        entry.delete()
        return Response({"message": "meal entry deleted, no servings left"}, status=200)


class ToggleMealEatenView(APIView):
    def post(self, request, entry_id):
        try:
            meal_entry = MealEntry.objects.get(id=entry_id)
            meal_entry.eaten = not meal_entry.eaten
            meal_entry.save()

            # Calculate nutritional values using correct field names
            total_calories = meal_entry.calories
            total_fats = meal_entry.fats_g
            total_carbs = meal_entry.carbs_g
            total_proteins = meal_entry.protein_g

            return Response({
                'eaten': meal_entry.eaten,
                'total_calories': total_calories,
                'total_fats': total_fats,
                'total_carbs': total_carbs,
                'total_proteins': total_proteins,
            }, status=status.HTTP_200_OK)
        except MealEntry.DoesNotExist:
            return Response({'error': 'Meal entry not found'}, status=status.HTTP_404_NOT_FOUND)
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='entry_id',
                description='ID of the meal entry to toggle',
                required=True,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
            ),
        ],
        request=None,
        responses={200: OpenApiTypes.OBJECT},
        description="Toggle the eaten status of a meal entry"
    )
    def patch(self, request, entry_id):
        user = request.user

        try:
            entry = MealEntry.objects.get(id=entry_id, user=user)
        except MealEntry.DoesNotExist:
            return Response({"error": "Entry not found"}, status=404)

        # Toggle the eaten status
        entry.eaten = not entry.eaten
        entry.save()

        # Calculate total consumed from all eaten meals for the day
        eaten_meals = MealEntry.objects.filter(user=user, date=entry.date, eaten=True)
        total_consumed = {
            "calories": sum(meal.calories for meal in eaten_meals),
            "protein_g": sum(meal.protein_g for meal in eaten_meals),
            "carbs_g": sum(meal.carbs_g for meal in eaten_meals),
            "fats_g": sum(meal.fats_g for meal in eaten_meals),
        }

        # Get nutrition targets based on user profile
        targets = calculate_nutrition_targets(user)

        # Get or create daily summary with calculated targets
        summary, _ = DailyNutritionSummary.objects.get_or_create(
            user=user,
            date=entry.date,
            defaults={
                "calories_target": targets["calories_target"],
                "protein_target": targets["protein_target"],
                "carbs_target": targets["carbs_target"],
                "fats_target": targets["fats_target"],
                "calories_consumed": total_consumed["calories"],
                "protein_g": total_consumed["protein_g"],
                "carbs_g": total_consumed["carbs_g"],
                "fats_g": total_consumed["fats_g"],
            },
        )

        # Update summary with current totals
        summary.calories_consumed = total_consumed["calories"]
        summary.protein_g = total_consumed["protein_g"]
        summary.carbs_g = total_consumed["carbs_g"]
        summary.fats_g = total_consumed["fats_g"]
        
        # Update targets if not already set
        if summary.calories_target == 0:
            summary.calories_target = targets["calories_target"]
            summary.protein_target = targets["protein_target"]
            summary.carbs_target = targets["carbs_target"]
            summary.fats_target = targets["fats_target"]
        
        summary.save()

        return Response(
            {
                "message": "Meal eaten status toggled",
                "entry": {
                    "id": entry.id,
                    "name": entry.name if entry.name else (entry.food.name if entry.food else "Unknown"),
                    "serving": entry.serving,
                    "quantity": entry.quantity,
                    "calories": entry.calories,
                    "protein_g": entry.protein_g,
                    "carbs_g": entry.carbs_g,
                    "fats_g": entry.fats_g,
                    "eaten": entry.eaten,
                },
                "daily_summary": {
                    "date": str(summary.date),
                    "calories": {
                        "consumed": summary.calories_consumed,
                        "target": summary.calories_target,
                        "remaining": max(summary.calories_target - summary.calories_consumed, 0),
                    },
                    "protein": {
                        "consumed": round(summary.protein_g, 1),
                        "target": round(summary.protein_target, 1),
                        "remaining": round(max(summary.protein_target - summary.protein_g, 0), 1),
                    },
                    "carbs": {
                        "consumed": round(summary.carbs_g, 1),
                        "target": round(summary.carbs_target, 1),
                        "remaining": round(max(summary.carbs_target - summary.carbs_g, 0), 1),
                    },
                    "fats": {
                        "consumed": round(summary.fats_g, 1),
                        "target": round(summary.fats_target, 1),
                        "remaining": round(max(summary.fats_target - summary.fats_g, 0), 1),
                    },
                },
            },
            status=200,
        )


#profile-overview
class ProfileOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        description="Get user's profile overview"
    )
    def get(self, request):
        user = request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)

        data = {
            "name": profile.name,
            "age": profile.age,
            "weight": profile.weight,
            "weight_unit": profile.weight_unit,
            "height_cm": profile.height_cm,
            "gender": profile.gender,
            "goal": profile.goal,
            "diet_preference": profile.diet_preference,
            "health_conditions": profile.health_conditions,
            "other_condition_text": profile.other_condition_text,
            "allergies": profile.allergies,
            "allergy_notes": profile.allergy_notes,
            "profile_image_url": (
                request.build_absolute_uri(profile.profile_image.url)
                if profile.profile_image
                else None
            ),
        }
        return Response(data, status=status.HTTP_200_OK)

    def put(self, request):
        user = request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)

        data = request.data

        profile.name = data.get("name", profile.name)
        profile.age = data.get("age", profile.age)
        profile.weight = data.get("weight", profile.weight)
        profile.weight_unit = data.get("weight_unit", profile.weight_unit or "kg")
        profile.height_cm = data.get("height_cm", profile.height_cm)
        profile.gender = data.get("gender", profile.gender)
        profile.goal = data.get("goal", profile.goal)
        profile.diet_preference = data.get("diet_preference", profile.diet_preference)
        profile.health_conditions = data.get(
            "health_conditions", profile.health_conditions
        )
        profile.other_condition_text = data.get(
            "other_condition_text", profile.other_condition_text
        )
        profile.allergies = data.get("allergies", profile.allergies)
        profile.allergy_notes = data.get("allergy_notes", profile.allergy_notes)
        profile.save()

        # Optional: mark onboarding completed
        user.onboarding_completed = True
        user.save(update_fields=["onboarding_completed"])

        return Response({"message": "Profile updated"}, status=status.HTTP_200_OK)

#upload-image
from rest_framework.parsers import MultiPartParser, FormParser

class ProfileImageUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    @extend_schema(
        request=OpenApiTypes.OBJECT,
        responses={200: OpenApiTypes.OBJECT},
        description="Upload or update user's profile image"
    )
    def put(self, request):
        user = request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)

        image_file = request.FILES.get("image")
        if not image_file:
            return Response(
                {"error": "image file is required (field name: image)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile.profile_image = image_file
        profile.save()

        image_url = request.build_absolute_uri(profile.profile_image.url)

        return Response(
            {"message": "Profile image updated", "profile_image_url": image_url},
            status=status.HTTP_200_OK,
        )


#profile-settings
class ProfileSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        description="Get user's app settings"
    )
    def get(self, request):
        user = request.user
        settings_obj, _ = UserAppSettings.objects.get_or_create(user=user)

        data = {
            "notifications_enabled": settings_obj.notifications_enabled,
            "meal_reminders_enabled": settings_obj.meal_reminders_enabled,
            "reminder_time": settings_obj.reminder_time.strftime("%H:%M")
            if settings_obj.reminder_time
            else None,
            "weekly_summary_enabled": settings_obj.weekly_summary_enabled,
        }
        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(
        request=OpenApiTypes.OBJECT,
        responses={200: OpenApiTypes.OBJECT},
        description="Update user's app settings"
    )
    def put(self, request):
        return self._update(request)

    def post(self, request):
        return self._update(request)

    def _update(self, request):
        user = request.user
        settings_obj, _ = UserAppSettings.objects.get_or_create(user=user)

        data = request.data

        if "notifications_enabled" in data:
            settings_obj.notifications_enabled = bool(data["notifications_enabled"])
        if "meal_reminders_enabled" in data:
            settings_obj.meal_reminders_enabled = bool(data["meal_reminders_enabled"])
        if "weekly_summary_enabled" in data:
            settings_obj.weekly_summary_enabled = bool(data["weekly_summary_enabled"])

        rt = data.get("reminder_time")
        if rt:
            # expect "HH:MM"
            from datetime import datetime

            try:
                settings_obj.reminder_time = datetime.strptime(rt, "%H:%M").time()
            except ValueError:
                return Response(
                    {"error": "Invalid reminder_time format, use HH:MM"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        settings_obj.save()

        return Response({"message": "Settings updated"}, status=status.HTTP_200_OK)

#help-support
class HelpSupportView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        description="Get FAQs and support contact information"
    )
    def get(self, request):
        data = {
            "faqs": [
                {
                    "question": "How do I change my goal?",
                    "answer": "Go to Profile > Overview and update your goal.",
                },
                {
                    "question": "Why are my calories zero?",
                    "answer": "Add meals from the Meals tab. Dashboard will auto-update.",
                },
            ],
            "contact_email": "support@dietapp.local",
            "contact_phone": "+91-90000-00000",
            "whatsapp": "+91-90000-00000"
        }
        return Response(data, status=status.HTTP_200_OK)

#delete account
class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        description="Delete user account and blacklist all tokens"
    )
    def delete(self, request):
        user = request.user

        # blacklist all tokens
        try:
            tokens = OutstandingToken.objects.filter(user=user)
            for token in tokens:
                BlacklistedToken.objects.get_or_create(token=token)
        except Exception:
            pass

        user_mobile = user.mobile
        user.delete()

        return Response(
            {"message": f"Account for {user_mobile} deleted"},
            status=status.HTTP_200_OK,
        )


#twillio
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from django.conf import settings
# import random
# from .models import OTP, User
# from .twilio_utils import send_otp_sms


# # ===================== SEND OTP =======================

# class SendOTPView(APIView):
#     permission_classes = []   # AllowAny

#     def post(self, request):
#         mobile = request.data.get("mobile")

#         if not mobile:
#             return Response({"error": "Mobile is required"}, status=status.HTTP_400_BAD_REQUEST)

#         # Format Validation
#         if not mobile.startswith("+"):
#             return Response(
#                 {"error": "Mobile must be in E.164 format e.g. +91XXXXXXXXXX"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         # CREATE OTP
#         otp_code = f"{random.randint(100000, 999999)}"

#         OTP.objects.update_or_create(
#             mobile=mobile,
#             is_used=False,
#             defaults={"code": otp_code}
#         )

#         # -------------- DEV MODE --------------
#         if settings.DEBUG:
#             print(f"[DEBUG] OTP for {mobile} = {otp_code}")
#             return Response(
#                 {"message": "OTP generated (TEST MODE)", "otp": otp_code},
#                 status=status.HTTP_200_OK
#             )

#         # ------------- PRODUCTION MODE (Twilio SMS) -------------
#         success = send_otp_sms(mobile, otp_code)

#         if not success:
#             return Response({"error": "Failed to send SMS"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)


# # ===================== VERIFY OTP =======================

# class VerifyOTPView(APIView):
#     permission_classes = []  # AllowAny

#     def post(self, request):
#         mobile = request.data.get("mobile")
#         otp = request.data.get("otp")

#         if not mobile or not otp:
#             return Response({"error": "Mobile and OTP required"}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             otp_obj = OTP.objects.get(mobile=mobile, code=otp, is_used=False)
#         except OTP.DoesNotExist:
#             return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)

#         otp_obj.is_used = True
#         otp_obj.save()

#         # ----------------- LOGIN / REGISTER USER -----------------
#         user, created = User.objects.get_or_create(username=mobile, mobile=mobile)

#         return Response(
#             {
#                 "message": "OTP verified successfully",
#                 "user_id": user.id,
#                 "is_new": created
#             },
#             status=status.HTTP_200_OK
#         )
