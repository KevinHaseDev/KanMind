from django.contrib import admin  
from django.contrib.auth.admin import UserAdmin 
from .models import CustomUser 

@admin.register(CustomUser)  
class CustomUserAdmin(UserAdmin):  
	model = CustomUser  
	ordering = ("email",)  
	list_display = ("email", "fullname", "is_staff", "is_superuser")  
	search_fields = ("email", "fullname")  

	fieldsets = (  
		(None, {"fields": ("email", "password")}),  
		("Personal info", {"fields": ("fullname", "first_name", "last_name")}),  
		(  
			"Permissions",  
			{"fields": (
				"is_active", 
				"is_staff", 
				"is_superuser", 
				"groups", 
				"user_permissions")},  
		),
		("Important dates", {"fields": ("last_login", "date_joined")}),  
	)
	add_fieldsets = (  
		(  
			None,  
			{  
				"classes": ("wide",),  
				"fields": (
					"email", 
					"fullname", 
					"password1", 
					"password2", 
					"is_staff", 
					"is_superuser"
				),  
			},
		),
	)
