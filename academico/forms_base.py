"""
Formulario base con estilos Bootstrap y mensajes de error en español.

Todos los formularios del sistema deben heredar de estos mixins para mantener
consistencia visual y de validación.
"""
from django import forms


class BaseFormMixin:
    """
    Mixin que agrega clases CSS de Bootstrap a todos los campos
    y configura mensajes de error en español.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aplicar_clases_bootstrap()
        self._configurar_mensajes_error()
    
    def _aplicar_clases_bootstrap(self):
        """Aplica clases CSS de Bootstrap a todos los campos del formulario."""
        for field_name, field in self.fields.items():
            # Determinar la clase CSS según el tipo de campo
            if isinstance(field.widget, (forms.Select, forms.ModelChoiceField)):
                css_class = 'form-select'
            elif isinstance(field.widget, forms.CheckboxInput):
                css_class = 'form-check-input'
            elif isinstance(field.widget, forms.Textarea):
                css_class = 'form-control'
            else:
                css_class = 'form-control'
            
            # Obtener attrs existentes o crear nuevos
            existing_class = field.widget.attrs.get('class', '')
            if css_class not in existing_class:
                field.widget.attrs['class'] = f'{css_class} {existing_class}'.strip()
    
    def _configurar_mensajes_error(self):
        """Configura mensajes de error por defecto en español."""
        mensajes_default = {
            'required': 'Este campo es obligatorio.',
            'invalid': 'El valor ingresado no es válido.',
            'invalid_choice': 'Seleccione una opción válida.',
        }
        
        for field_name, field in self.fields.items():
            for error_key, error_msg in mensajes_default.items():
                if error_key not in field.error_messages:
                    field.error_messages[error_key] = error_msg


class BaseModelForm(BaseFormMixin, forms.ModelForm):
    """
    Formulario base para modelos con estilos Bootstrap y mensajes en español.
    
    Uso:
        class MiFormulario(BaseModelForm):
            class Meta:
                model = MiModelo
                fields = ['campo1', 'campo2']
    """
    pass


class BaseForm(BaseFormMixin, forms.Form):
    """
    Formulario base no vinculado a modelos con estilos Bootstrap.
    
    Uso:
        class MiFormulario(BaseForm):
            campo1 = forms.CharField()
    """
    pass


def add_form_control_class(field, css_class='form-control'):
    """
    Función auxiliar para agregar clase form-control a un campo específico.
    Útil cuando se sobreescriben widgets en Meta.
    """
    existing = field.widget.attrs.get('class', '')
    if css_class not in existing:
        field.widget.attrs['class'] = f'{css_class} {existing}'.strip()
