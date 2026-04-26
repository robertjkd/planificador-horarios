from django.urls import path
from . import views

app_name = 'planificacion'

urlpatterns = [
    path('importar-balance/', views.importar_balance_view, name='importar_balance'),
    path('generar/', views.seleccionar_generacion, name='seleccionar_generacion'),
    path('generar/<int:anio_id>/<int:semana>/', views.generar_horario_view, name='generar'),
]
