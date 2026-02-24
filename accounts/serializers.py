from rest_framework import serializers
from .models import (
    UserProfile, MealEntry, DailyNutritionSummary, 
    UserAppSettings, OTP, MealRecommendation, 
    WeeklyMealRecommendation
)

class SendOTPSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=15, required=True)

class VerifyOTPSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=15, required=True)
    otp = serializers.CharField(max_length=6, required=True)

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'name', 'age', 'weight', 'weight_unit', 'height_cm', 
            'gender', 'goal', 'diet_preference', 'target_weight',
            'health_conditions', 'other_condition_text', 'allergies', 'allergy_notes', 'profile_image'
        ]
        read_only_fields = ['user']

class OnboardingSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    age = serializers.IntegerField(required=False, allow_null=True)
    weight = serializers.FloatField()
    weight_unit = serializers.CharField(default="kg")
    height_cm = serializers.FloatField()
    gender = serializers.CharField(required=False, allow_null=True)
    goal = serializers.CharField()
    diet_preference = serializers.CharField()
    health_conditions = serializers.ListField(child=serializers.CharField(), required=False)
    other_condition_text = serializers.CharField(required=False, allow_blank=True)
    allergies = serializers.ListField(child=serializers.CharField(), required=False)
    allergy_notes = serializers.CharField(required=False, allow_blank=True)
    target_weight = serializers.FloatField(required=False, allow_null=True)

class MealEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = MealEntry
        fields = [
            'id', 'date', 'meal_type', 'name', 'serving', 
            'quantity', 'calories', 'protein_g', 'carbs_g', 'fats_g', 'eaten'
        ]

class AddMealEntrySerializer(serializers.Serializer):
    date = serializers.DateField()
    meal_type = serializers.ChoiceField(choices=MealEntry.MEAL_TYPES)
    name = serializers.CharField()
    serving = serializers.CharField(required=False, allow_blank=True)
    calories = serializers.FloatField()
    protein_g = serializers.FloatField(required=False)
    carbs_g = serializers.FloatField(required=False)
    fats_g = serializers.FloatField(required=False)
    quantity = serializers.FloatField(default=1.0)

class DailyNutritionSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyNutritionSummary
        fields = [
            'date', 'user_name', 'calories_target', 'calories_consumed', 
            'protein_g', 'protein_target', 'carbs_g', 'carbs_target', 'fats_g', 'fats_target'
        ]

class UserAppSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAppSettings
        fields = [
            'notifications_enabled', 'meal_reminders_enabled', 
            'reminder_time', 'weekly_summary_enabled'
        ]


class MealItemSerializer(serializers.Serializer):
    """Serializer for individual meal items in recommendations"""
    name = serializers.CharField()
    serving = serializers.CharField()
    calories = serializers.IntegerField()
    protein_g = serializers.FloatField()
    carbs_g = serializers.FloatField()
    fats_g = serializers.FloatField()
    note = serializers.CharField(required=False, allow_blank=True)
    image_url = serializers.URLField(required=False, allow_blank=True)

class MealRecommendationSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    
    class Meta:
        model = MealRecommendation
        fields = [
            'date', 'meal_type', 'goal', 'diet_preference', 
            'health_conditions', 'target_calories', 'items', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_items(self, obj):
        """Return items with all nutritional and image data"""
        return obj.items_json

class WeeklyMealRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeeklyMealRecommendation
        fields = ['week_start_date', 'user_name', 'recommendations_data', 'created_at']