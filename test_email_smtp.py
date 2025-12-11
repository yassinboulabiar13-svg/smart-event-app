import os
import django
from django.conf import settings
from django.core.mail import send_mail

# Configuration de l'environnement
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_event.settings')
django.setup()

def test_send_email():
    print("\n=== TEST D'ENVOI D'EMAIL AVEC SMTP/SSL ===")
    
    # Configuration de test
    subject = 'Test d\'envoi depuis Django (SSL)'
    message = 'Ceci est un test d\'envoi d\'email avec SSL depuis Django.'
    from_email = 'Smart Event <yassinboulabiar13@gmail.com>'
    recipient_list = ['yassinboulabiar13@gmail.com']
    
    print(f"\nConfiguration utilisée :")
    print(f"Serveur: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
    print(f"Utilisateur: {settings.EMAIL_HOST_USER}")
    print(f"SSL: {settings.EMAIL_USE_SSL}")
    print(f"TLS: {settings.EMAIL_USE_TLS}")
    print(f"De: {from_email}")
    print(f"À: {recipient_list}")
    
    try:
        print("\nEnvoi de l'email...")
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        print("\n✅ Email envoyé avec succès !")
        print("Vérifiez votre boîte de réception et le dossier spam.")
    except Exception as e:
        print(f"\n❌ Erreur lors de l'envoi de l'email : {str(e)}")
        print("\nVérifiez :")
        print("1. Que votre mot de passe est correct")
        print("2. Que l'accès aux applications moins sécurisées est activé")
        print("3. Que le port 465 n'est pas bloqué par votre pare-feu")

if __name__ == "__main__":
    test_send_email()
