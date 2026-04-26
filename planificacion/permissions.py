from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages


def rol_requerido(*roles):
    """
    Decorador que restringe el acceso a usuarios con el rol especificado.
    Uso: @rol_requerido('VICEDECANO', 'PLANIFICADOR')
    
    Redirige al login si no está autenticado.
    Muestra mensaje de error y redirige a home si no tiene el rol requerido.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('usuarios:login')
            if request.user.rol in roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, 'No tiene permisos para acceder a esta página.')
            return redirect('usuarios:home')
        return _wrapped_view
    return decorator


def vicedecano_required(view_func):
    """Decorador que requiere rol VICEDECANO."""
    return rol_requerido('VICEDECANO')(view_func)


def planificador_required(view_func):
    """Decorador que requiere rol PLANIFICADOR o superior."""
    return rol_requerido('VICEDECANO', 'PLANIFICADOR')(view_func)


def consulta_required(view_func):
    """Decorador que requiere cualquier rol autenticado."""
    return rol_requerido('VICEDECANO', 'PLANIFICADOR', 'CONSULTA')(view_func)


class RolesRequeridosMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin para vistas basadas en clases (CBV) que requiere roles específicos.
    
    Uso:
        class MiVista(RolesRequeridosMixin, CreateView):
            roles_permitidos = ['VICEDECANO', 'PLANIFICADOR']
            ...
    
    Si el usuario no tiene el rol requerido, redirige a home con mensaje de error.
    """
    roles_permitidos = []
    
    def test_func(self):
        """Verifica si el usuario tiene uno de los roles permitidos."""
        return self.request.user.rol in self.roles_permitidos
    
    def handle_no_permission(self):
        """Maneja el caso cuando el usuario no tiene permisos."""
        if not self.request.user.is_authenticated:
            return redirect('usuarios:login')
        messages.error(self.request, 'No tiene permisos para acceder a esta página.')
        return redirect('usuarios:home')


class VicedecanoRequiredMixin(RolesRequeridosMixin):
    """Mixin que requiere rol VICEDECANO."""
    roles_permitidos = ['VICEDECANO']


class PlanificadorRequiredMixin(RolesRequeridosMixin):
    """Mixin que requiere rol PLANIFICADOR o superior."""
    roles_permitidos = ['VICEDECANO', 'PLANIFICADOR']


class ConsultaRequiredMixin(RolesRequeridosMixin):
    """Mixin que requiere cualquier rol autenticado."""
    roles_permitidos = ['VICEDECANO', 'PLANIFICADOR', 'CONSULTA']
