from django.contrib import admin
from .models import Company, AssignmentConfig, Billing, Invoice

admin.site.register(Company)
admin.site.register(AssignmentConfig)
admin.site.register(Billing)
admin.site.register(Invoice)
