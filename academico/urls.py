from django.urls import path
from . import views

app_name = 'academico'

urlpatterns = [
    # Años Académicos
    path('annos/', views.anno_list, name='anno_list'),
    path('annos/crear/', views.anno_create, name='anno_create'),
    path('annos/<int:pk>/editar/', views.anno_update, name='anno_update'),
    path('annos/<int:pk>/eliminar/', views.anno_delete, name='anno_delete'),
    
    # Grupos
    path('grupos/', views.grupo_list, name='grupo_list'),
    path('grupos/crear/', views.grupo_create, name='grupo_create'),
    path('grupos/<int:pk>/editar/', views.grupo_update, name='grupo_update'),
    path('grupos/<int:pk>/eliminar/', views.grupo_delete, name='grupo_delete'),
    
    # Locales
    path('locales/', views.local_list, name='local_list'),
    path('locales/crear/', views.local_create, name='local_create'),
    path('locales/<int:pk>/editar/', views.local_update, name='local_update'),
    path('locales/<int:pk>/eliminar/', views.local_delete, name='local_delete'),
    
    # Franjas Horarias
    path('franjas/', views.franjahoraria_list, name='franjahoraria_list'),
    path('franjas/crear/', views.franjahoraria_create, name='franjahoraria_create'),
    path('franjas/<int:pk>/editar/', views.franjahoraria_update, name='franjahoraria_update'),
    path('franjas/<int:pk>/eliminar/', views.franjahoraria_delete, name='franjahoraria_delete'),
    
    # Asignaturas
    path('asignaturas/', views.asignatura_list, name='asignatura_list'),
    path('asignaturas/crear/', views.asignatura_create, name='asignatura_create'),
    path('asignaturas/<int:pk>/editar/', views.asignatura_update, name='asignatura_update'),
    path('asignaturas/<int:pk>/eliminar/', views.asignatura_delete, name='asignatura_delete'),
    
    # Profesores
    path('profesores/', views.profesor_list, name='profesor_list'),
    path('profesores/crear/', views.profesor_create, name='profesor_create'),
    path('profesores/<int:pk>/editar/', views.profesor_update, name='profesor_update'),
    path('profesores/<int:pk>/eliminar/', views.profesor_delete, name='profesor_delete'),
    
    # Asignaciones Profesor-Asignatura
    path('asignaciones-profesor/', views.asignacionprofesor_list, name='asignacionprofesor_list'),
    path('asignaciones-profesor/crear/', views.asignacionprofesor_create, name='asignacionprofesor_create'),
    path('asignaciones-profesor/<int:pk>/editar/', views.asignacionprofesor_update, name='asignacionprofesor_update'),
    path('asignaciones-profesor/<int:pk>/eliminar/', views.asignacionprofesor_delete, name='asignacionprofesor_delete'),
    
    # Asignaciones Aula-Grupo
    path('asignaciones-aula/', views.asignacionaulagrupo_list, name='asignacionaulagrupo_list'),
    path('asignaciones-aula/crear/', views.asignacionaulagrupo_create, name='asignacionaulagrupo_create'),
    path('asignaciones-aula/<int:pk>/editar/', views.asignacionaulagrupo_update, name='asignacionaulagrupo_update'),
    path('asignaciones-aula/<int:pk>/eliminar/', views.asignacionaulagrupo_delete, name='asignacionaulagrupo_delete'),
    
    # Panel Auditoría
    path('panel-auditoria/', views.panel_auditoria, name='panel_auditoria'),
]
