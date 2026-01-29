from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTP, LoginHistory
from .models import DailyNutritionSummary
from .models import Food, MealEntry



@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('mobile', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
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
    list_display = ('id', 'mobile', 'onboarding_completed', 'is_active')
    search_fields = ('mobile',)
    ordering = ('id',)


admin.site.register(OTP)






# 👇 New: LoginHistory admin
@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "get_user_name", "is_new_user", "logged_at")
    list_filter = ("is_new_user", "logged_at")
    search_fields = ("user__mobile", "user__profile__name")
    
    def get_user_name(self, obj):
        return obj.user.user_name
    get_user_name.short_description = "User"

@admin.register(DailyNutritionSummary)
class DailyNutritionSummaryAdmin(admin.ModelAdmin):
    list_display = ("get_user_name", "user", "date", "calories_target", "calories_consumed",
                    "protein_g", "carbs_g", "fats_g")
    list_filter = ("date",)
    search_fields = ("user__mobile", "user__profile__name")
    
    def get_user_name(self, obj):
        return obj.get_user_name()
    get_user_name.short_description = "Name"

@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ("name", "serving", "calories", "protein_g", "carbs_g", "fats_g")


@admin.register(MealEntry)
class MealEntryAdmin(admin.ModelAdmin):
    list_display = ("get_user_name", "user", "date", "meal_type", "food", "calories")
    list_filter = ("meal_type", "date")
    search_fields = ("user__mobile", "user__profile__name")
    
    def get_user_name(self, obj):
        return obj.get_user_name()
    get_user_name.short_description = "Name"
