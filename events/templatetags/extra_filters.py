from django import template

register = template.Library()

@register.filter
def get_username(email):
    """
    Extrait le nom d'utilisateur d'une adresse email (partie avant le @)
    """
    return email.split('@')[0] if email and '@' in email else email
