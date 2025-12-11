from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import TwoFactorAuth, UserProfile

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Crée automatiquement un profil utilisateur et une configuration 2FA
    lors de la création d'un nouvel utilisateur
    """
    if created:
        # Créer le profil utilisateur
        UserProfile.objects.create(user=instance)
        
        # Créer la configuration 2FA (désactivée par défaut)
        TwoFactorAuth.objects.create(user=instance, is_enabled=False)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Sauvegarde automatiquement le profil utilisateur lors de la sauvegarde de l'utilisateur
    """
    instance.userprofile.save()
    
    # S'assurer qu'il y a une configuration 2FA pour l'utilisateur
    if not hasattr(instance, 'two_factor_auth'):
        TwoFactorAuth.objects.create(user=instance, is_enabled=False)
