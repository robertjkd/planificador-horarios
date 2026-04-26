from django.contrib import admin
from .models import (
    AnioAcademico,
    Grupo,
    Profesor,
    Local,
    FranjaHoraria,
    Asignatura,
    AsignacionProfesor,
    ActividadPlan,
    Asignacion,
)


@admin.register(AnioAcademico)
class AnioAcademicoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'turno')
    list_filter = ('turno',)
    search_fields = ('numero',)


@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'anio', 'cantidad_alumnos')
    list_filter = ('anio',)
    search_fields = ('nombre',)


@admin.register(Profesor)
class ProfesorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'usuario')
    search_fields = ('nombre',)


@admin.register(Local)
class LocalAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'tipo', 'capacidad')
    list_filter = ('tipo',)
    search_fields = ('codigo', 'nombre')


@admin.register(FranjaHoraria)
class FranjaHorariaAdmin(admin.ModelAdmin):
    list_display = ('turno', 'orden', 'hora_inicio', 'hora_fin')
    list_filter = ('turno',)
    ordering = ('turno', 'orden')


@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'abreviatura', 'anio')
    list_filter = ('anio',)
    search_fields = ('nombre', 'abreviatura')


@admin.register(AsignacionProfesor)
class AsignacionProfesorAdmin(admin.ModelAdmin):
    list_display = ('profesor', 'asignatura', 'grupo', 'tipo_actividad')
    list_filter = ('tipo_actividad', 'asignatura__anio')
    search_fields = ('profesor__nombre', 'asignatura__nombre')


@admin.register(ActividadPlan)
class ActividadPlanAdmin(admin.ModelAdmin):
    list_display = ('asignatura', 'tipo_actividad', 'grupo', 'anio', 'semana', 'dia_semana', 'requiere_local')
    list_filter = ('anio', 'tipo_actividad', 'semana', 'dia_semana')
    search_fields = ('asignatura__nombre',)


@admin.register(Asignacion)
class AsignacionAdmin(admin.ModelAdmin):
    list_display = ('actividad_plan', 'franja', 'local', 'profesor', 'manual')
    list_filter = ('manual',)
    search_fields = ('actividad_plan__asignatura__nombre',)
