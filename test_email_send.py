import os
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_event.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

def test_send_email():
    print("\n=== TEST D'ENVOI D'EMAIL ===")
    print(f"EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Non défini')}")
    print(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Non défini')}")
    print(f"EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Non défini')}")
    print(f"EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Non défini')}")
    print(f"EMAIL_USE_SSL: {getattr(settings, 'EMAIL_USE_SSL', 'Non défini')}")
    print(f"EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'Non défini')}")
    print(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Non défini')}")
    
    subject = 'Test d\'envoi d\'email depuis Django'
    message = 'Ceci est un test d\'envoi d\'email depuis Django.'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = ['yassinboulabiar13@gmail.com']  # Votre adresse email
    
    try:
        print(f"\nEnvoi d'un email à {recipient_list}...")
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False,
        )
        print("✅ Email envoyé avec succès !")
        print("Vérifiez votre boîte de réception et le dossier spam.")
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de l'email : {str(e)}")
        print("Veuillez vérifier votre configuration SMTP dans settings.py")

if __name__ == "__main__":
    test_send_email()
