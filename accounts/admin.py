from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, OTP, LoginHistory, UserProfile, 
    DailyNutritionSummary, MealEntry, 
    MealRecommendation, WeeklyMealRecommendation
)

# Rename the Admin Site
admin.site.site_header = "Diet Planner"
admin.site.site_title = "Diet Planner Admin Portal"
admin.site.index_title = "Welcome to Diet Planner Management"

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile Details'
    fk_name = 'user'

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    fieldsets = (
        (None, {'fields': ('mobile', 'password')}),
        ('Diet App', {'fields': ('onboarding_completed',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('mobile', 'password1', 'password2'),
        }),
    )
    list_display = ('id', 'mobile', 'onboarding_completed', 'is_staff', 'is_superuser')
    search_fields = ('mobile',)
    ordering = ('id',)

    # Show only superadmins in the user list
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(is_superuser=True)

@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ("mobile", "code", "created_at", "is_used")
    search_fields = ("mobile",)

@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "get_user_name", "mobile", "is_new_user", "logged_at")
    list_filter = ("is_new_user", "logged_at")
    search_fields = ("user__mobile", "user_name")
    
    def get_user_name(self, obj):
        return obj.get_user_name()
    get_user_name.short_description = "Name"

@admin.register(DailyNutritionSummary)
class DailyNutritionSummaryAdmin(admin.ModelAdmin):
    list_display = ("get_user_name", "user_name", "user", "date", "calories_target", "calories_consumed")
    list_filter = ("date",)
    search_fields = ("user__mobile", "user_name")
    
    def get_user_name(self, obj):
        return obj.get_user_name()
    get_user_name.short_description = "Name"


@admin.register(MealEntry)
class MealEntryAdmin(admin.ModelAdmin):
    list_display = ("get_user_name", "user_name", "user", "date", "meal_type", "name", "calories", "eaten")
    list_filter = ("meal_type", "date", "eaten")
    search_fields = ("user__mobile", "name", "user_name")
    
    def get_user_name(self, obj):
        return obj.get_user_name()
    get_user_name.short_description = "Name"

@admin.register(MealRecommendation)
class MealRecommendationAdmin(admin.ModelAdmin):
    list_display = ("get_user_name", "user", "date", "meal_type", "created_at")
    list_filter = ("meal_type", "date")
    search_fields = ("user__mobile", "user_name")

    def get_user_name(self, obj):
        return obj.get_user_name()
    get_user_name.short_description = "Name"

@admin.register(WeeklyMealRecommendation)
class WeeklyMealRecommendationAdmin(admin.ModelAdmin):
    list_display = ("get_user_name", "user", "week_start_date", "created_at")
    list_filter = ("week_start_date",)
    search_fields = ("user__mobile", "user_name")

    def get_user_name(self, obj):
        return obj.get_user_name()
    get_user_name.short_description = "Name"

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user", "name", "age", "gender", "weight", "height_cm", 
        "goal", "diet_preference", "target_weight", "updated_at"
    )
    list_filter = ("gender", "goal", "diet_preference")
    search_fields = ("user__mobile", "name")
    readonly_fields = ("updated_at",)
