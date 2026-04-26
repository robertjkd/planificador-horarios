from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect


class RolRequiredMixin(AccessMixin):
    roles_permitidos = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.rol not in self.roles_permitidos:
            return redirect('usuarios:home')
        return super().dispatch(request, *args, **kwargs)


class VicedecanoMixin(RolRequiredMixin):
    roles_permitidos = ['VICEDECANO']


class PlanificadorMixin(RolRequiredMixin):
    roles_permitidos = ['VICEDECANO', 'PLANIFICADOR']
