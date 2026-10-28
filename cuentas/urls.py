from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('encuesta/<int:paso>/', views.encuesta, name='encuesta'),
    path('diagnostico/', views.diagnostico, name='diagnostico'),
    path('plan/', views.plan, name='plan'),
    path('plan/generar/', views.crear_plan, name='generar_plan'),
    path('accion/<int:accion_id>/', views.accion, name='accion'),
    path('progreso/', views.seguimiento, name='seguimiento'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro, name='registro'),
    path('logout/', views.logout_view, name='logout'),
]