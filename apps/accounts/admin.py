from django.contrib import admin
from .models import User, InviteToken

admin.site.register(User)
admin.site.register(InviteToken)
