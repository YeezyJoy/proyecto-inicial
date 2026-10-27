from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('diagnostico/', views.diagnostico, name='diagnostico'),
    path('plan/', views.plan, name='plan'),
    path('accion/', views.accion, name='accion'),
    path('progreso/', views.seguimiento, name='seguimiento'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro, name='registro'),
    path('logout/', views.logout_view, name='logout'),
]