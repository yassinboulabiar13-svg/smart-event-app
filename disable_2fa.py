import os
import django

def disable_2fa_for_user(username):
    """Désactive la 2FA pour un utilisateur spécifique"""
    from django.contrib.auth import get_user_model
    from events.models import TwoFactorAuth
    
    User = get_user_model()
    
    try:
        user = User.objects.get(username=username)
        two_fa, created = TwoFactorAuth.objects.get_or_create(user=user)
        two_fa.is_enabled = False
        two_fa.save()
        print(f"2FA a été désactivée pour l'utilisateur: {username}")
        return True
    except User.DoesNotExist:
        print(f"Erreur: L'utilisateur {username} n'existe pas.")
        return False

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_event.settings')
    django.setup()
    
    # Désactiver la 2FA pour l'utilisateur admin
    disable_2fa_for_user('admin')
    
    # Vous pouvez ajouter d'autres utilisateurs si nécessaire
    # disable_2fa_for_user('autre_utilisateur')
