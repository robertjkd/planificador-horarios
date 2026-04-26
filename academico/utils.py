"""
Utilidades para el sistema de auditoría y alertas.
"""
import logging
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Auditoria, TipoAccionAuditoria

logger_auditoria = logging.getLogger('auditoria')


def registrar_auditoria(usuario, accion, detalles='', request=None):
    """
    Registra una acción de auditoría tanto en base de datos como en log.
    
    Args:
        usuario: Instancia de Usuario o None
        accion: TipoAccionAuditoria o string del choice
        detalles: String con detalles adicionales
        request: Objeto HttpRequest para extraer IP y navegador
    """
    # Registrar en base de datos
    registro_db = Auditoria.registrar(usuario, accion, detalles, request)
    
    # Registrar en log de auditoría
    usuario_str = usuario.username if usuario else 'Sistema'
    ip_str = registro_db.ip_address if registro_db.ip_address else 'N/A'
    
    mensaje_log = f"{usuario_str} | {accion} | {ip_str} | {detalles}"
    logger_auditoria.info(mensaje_log)
    
    return registro_db


def verificar_fallos_solver_y_alertar():
    """
    Verifica si ha habido demasiados fallos del solver en el período configurado
    y envía alerta por correo si se supera el umbral.
    
    Returns:
        bool: True si se envió alerta, False en caso contrario
    """
    umbral = getattr(settings, 'SOLVER_FAILURE_THRESHOLD', 3)
    ventana_horas = getattr(settings, 'SOLVER_FAILURE_WINDOW_HOURS', 1)
    
    # Calcular fecha límite
    fecha_limite = timezone.now() - timedelta(hours=ventana_horas)
    
    # Contar fallos recientes
    fallos_recientes = Auditoria.objects.filter(
        accion=TipoAccionAuditoria.ERROR_SOLVER,
        fecha__gte=fecha_limite
    ).count()
    
    if fallos_recientes >= umbral:
        # Enviar alerta por correo
        asunto = f'⚠️ Alerta: {fallos_recientes} fallos del solver en las últimas {ventana_horas} horas'
        mensaje = f"""
Se han detectado {fallos_recientes} fallos del motor de optimización en las últimas {ventana_horas} horas.

Detalles de los fallos recientes:
"""
        
        # Obtener detalles de los fallos
        fallos = Auditoria.objects.filter(
            accion=TipoAccionAuditoria.ERROR_SOLVER,
            fecha__gte=fecha_limite
        ).order_by('-fecha')
        
        for fallo in fallos:
            mensaje += f"\n- {fallo.fecha.strftime('%Y-%m-%d %H:%M:%S')}: {fallo.detalles}\n"
        
        mensaje += "\nPor favor, revise los logs y la configuración del sistema."
        
        # Enviar a administradores
        admin_emails = [email for name, email in settings.ADMINS]
        
        try:
            send_mail(
                asunto,
                mensaje,
                settings.DEFAULT_FROM_EMAIL,
                admin_emails,
                fail_silently=False,
            )
            logger_auditoria.warning(f"Alerta enviada: {fallos_recientes} fallos del solver")
            return True
        except Exception as e:
            logger_auditoria.error(f"Error al enviar alerta por correo: {str(e)}")
            return False
    
    return False
