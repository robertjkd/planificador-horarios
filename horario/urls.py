from django.urls import path
from . import views

app_name = 'horario'

urlpatterns = [
    path('', views.ver_horario, name='ver_horario'),
    path('calendario/', views.ver_horario_calendario, name='ver_horario_calendario'),
    path('exportar/', views.exportar_horario, name='exportar_horario'),
    path('editar/<int:asignacion_id>/', views.editar_asignacion, name='editar_asignacion'),
    
    # API endpoints for FullCalendar
    path('api/horario/', views.api_horario, name='api_horario'),
    path('api/asignacion/<int:asignacion_id>/modificar/', views.api_modificar_asignacion, name='api_modificar_asignacion'),
    path('api/franjas/', views.api_franjas, name='api_franjas'),
    path('api/locales/', views.api_locales, name='api_locales'),
    path('api/profesores/', views.api_profesores, name='api_profesores'),
]
