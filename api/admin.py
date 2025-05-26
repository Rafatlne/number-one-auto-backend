from django.contrib import admin
from .models import User
from django.contrib.auth.admin import UserAdmin
from django.db import models

admin.site.register(User, UserAdmin)

