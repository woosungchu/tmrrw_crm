from django.urls import path
from . import views

urlpatterns = [
    path('', views.app_home, name='app_home'),
    path('invite/', views.invite_list, name='invite_list'),
    path('blocked/', views.blocked_page, name='blocked_page'),
]
