from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Accede a un diccionario por clave."""
    return dictionary.get(key) if dictionary else None


@register.filter
def get_nested_item(dictionary, key1, key2):
    """Accede a un diccionario anidado por dos claves."""
    if dictionary:
        d1 = dictionary.get(key1)
        return d1.get(key2) if d1 else None
    return None


@register.filter
def get_triple_nested(dictionary, key1, key2, key3):
    """Accede a un diccionario anidado por tres claves."""
    if dictionary:
        d1 = dictionary.get(key1)
        if d1:
            d2 = d1.get(key2)
            return d2.get(key3) if d2 else None
    return None
