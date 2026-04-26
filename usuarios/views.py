from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .models import Usuario
from .forms import UsuarioCreationForm, UsuarioChangeForm
from academico.utils import registrar_auditoria
from academico.models import TipoAccionAuditoria
from planificacion.permissions import vicedecano_required


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Registrar auditoría de inicio de sesión
            registrar_auditoria(
                user,
                TipoAccionAuditoria.INICIO_SESION,
                f"Usuario {user.username} inició sesión",
                request
            )
            
            return redirect('usuarios:home')
    else:
        form = AuthenticationForm()
    return render(request, 'usuarios/login.html', {'form': form})


def logout_view(request):
    user = request.user if request.user.is_authenticated else None
    logout(request)
    
    # Registrar auditoría de cierre de sesión
    if user:
        registrar_auditoria(
            user,
            TipoAccionAuditoria.CIERRE_SESION,
            f"Usuario {user.username} cerró sesión",
            request
        )
    
    return redirect('usuarios:login')


@login_required
def home(request):
    return render(request, 'home.html')


@vicedecano_required
def usuario_list(request):
    usuarios = Usuario.objects.all()
    return render(request, 'usuarios/usuario_list.html', {'usuarios': usuarios})


@vicedecano_required
def usuario_create(request):
    if request.method == 'POST':
        form = UsuarioCreationForm(request.POST)
        if form.is_valid():
            # Validar que no se esté intentando crear otro Vicedecano
            if form.cleaned_data.get('rol') == Usuario.Rol.VICEDECANO:
                messages.error(request, 'No se puede crear otro usuario con rol Vicedecano.')
                return render(request, 'usuarios/usuario_form.html', {'form': form, 'action': 'Crear'})

            usuario = form.save()

            # Detectar si se generaron credenciales automáticamente
            username_original = request.POST.get('username', '').strip()
            password_original = request.POST.get('password1', '').strip()

            # Mensaje de éxito con credenciales
            if not username_original and not password_original:
                # Ambos se generaron automáticamente
                messages.success(
                    request,
                    f'Usuario creado exitosamente. '
                    f'Username generado: <strong>{usuario.username}</strong> | '
                    f'Contraseña generada: <strong>{form.cleaned_data.get("password1")}</strong>. '
                    f'Guarde estas credenciales.'
                )
            elif not username_original:
                # Solo username se generó automáticamente
                messages.success(
                    request,
                    f'Usuario creado exitosamente. '
                    f'Username generado: <strong>{usuario.username}</strong>'
                )
            elif not password_original:
                # Solo password se generó automáticamente
                messages.success(
                    request,
                    f'Usuario creado exitosamente. '
                    f'Contraseña generada: <strong>{form.cleaned_data.get("password1")}</strong>. '
                    f'Guarde esta contraseña.'
                )
            else:
                # Credenciales manuales
                messages.success(request, f'Usuario {usuario.username} creado exitosamente.')

            # Registrar auditoría
            detalles = f"Usuario creado: {usuario.username}, rol: {usuario.get_rol_display()}"
            registrar_auditoria(
                request.user,
                TipoAccionAuditoria.CREAR_USUARIO,
                detalles,
                request
            )

            return redirect('usuarios:usuario_list')
    else:
        form = UsuarioCreationForm()
    return render(request, 'usuarios/usuario_form.html', {'form': form, 'action': 'Crear'})


@vicedecano_required
def usuario_update(request, pk):
    usuario = Usuario.objects.get(pk=pk)
    rol_anterior = usuario.get_rol_display()
    
    if request.method == 'POST':
        form = UsuarioChangeForm(request.POST, instance=usuario)
        if form.is_valid():
            # Validar que no se esté intentando asignar rol Vicedecano
            if form.cleaned_data.get('rol') == Usuario.Rol.VICEDECANO:
                messages.error(request, 'No se puede asignar el rol Vicedecano a otro usuario.')
                return render(request, 'usuarios/usuario_form.html', {'form': form, 'action': 'Editar'})
            
            # Guardar cambios antiguos para auditoría
            cambios = []
            if 'rol' in form.changed_data:
                cambios.append(f"Rol: {rol_anterior} → {form.cleaned_data.get('rol')}")
            if 'username' in form.changed_data:
                cambios.append(f"Username: {usuario.username} → {form.cleaned_data.get('username')}")
            
            form.save()
            
            # Registrar auditoría
            detalles = f"Usuario {usuario.username} editado. Cambios: {', '.join(cambios) if cambios else 'Ninguno'}"
            registrar_auditoria(
                request.user,
                TipoAccionAuditoria.EDITAR_USUARIO,
                detalles,
                request
            )
            
            return redirect('usuarios:usuario_list')
    else:
        form = UsuarioChangeForm(instance=usuario)
    return render(request, 'usuarios/usuario_form.html', {'form': form, 'action': 'Editar'})


@vicedecano_required
def usuario_delete(request, pk):
    usuario = Usuario.objects.get(pk=pk)
    # Protección: no se puede eliminar un Vicedecano
    if usuario.es_vicedecano:
        messages.error(request, 'No se puede eliminar un usuario con rol Vicedecano.')
        return redirect('usuarios:usuario_list')
    if request.method == 'POST':
        username = usuario.username
        usuario.delete()
        
        # Registrar auditoría
        detalles = f"Usuario eliminado: {username}"
        registrar_auditoria(
            request.user,
            TipoAccionAuditoria.ELIMINAR_USUARIO,
            detalles,
            request
        )

        messages.success(request, f'Usuario {username} eliminado exitosamente.')
        return redirect('usuarios:usuario_list')
    return render(request, 'usuarios/usuario_confirm_delete.html', {'usuario': usuario})
