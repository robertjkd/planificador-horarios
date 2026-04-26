import os

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from academico.models import AnioAcademico


class ImportarBalanceForm(forms.Form):
    """
    Formulario para subir el archivo de balance de carga.
    """
    anio = forms.ModelChoiceField(
        queryset=AnioAcademico.objects.all(),
        label=_('Año académico'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text=_('Seleccione el año al que corresponde el balance.'),
    )
    archivo = forms.FileField(
        label=_('Archivo de balance'),
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv,.xlsx'}),
        help_text=_('Formatos permitidos: CSV o Excel (.xlsx).'),
    )
    limpiar_previos = forms.BooleanField(
        required=False,
        initial=False,
        label=_('Eliminar actividades previas de este año'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_('Si se marca, se eliminarán todas las ActividadPlan del año antes de importar.'),
    )
    crear_asignaturas = forms.BooleanField(
        required=False,
        initial=False,
        label=_('Crear asignaturas automáticamente'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_('Si una asignatura del archivo no existe, se creará con abreviatura igual al nombre.'),
    )

    def clean_archivo(self):
        archivo = self.cleaned_data['archivo']
        ext = os.path.splitext(archivo.name)[1].lower()
        if ext not in ('.csv', '.xlsx'):
            raise ValidationError(_('Solo se permiten archivos .csv o .xlsx'))
        if archivo.size > 10 * 1024 * 1024:
            raise ValidationError(_('El archivo no puede superar los 10 MB.'))
        return archivo
