from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_username(email):
    """
    Extrait le nom d'utilisateur d'une adresse email (partie avant le @)
    """
    if not email or '@' not in str(email):
        return email
    return str(email).split('@')[0]
