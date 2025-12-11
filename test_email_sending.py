"""
Script pour tester l'envoi d'emails en mode production.
Exécutez ce script avec : python test_email_sending.py
"""
import os
import django

def test_email_sending():
    """Teste l'envoi d'un email de test"""
    from django.core.mail import send_mail
    from django.conf import settings
    
    subject = 'Test d\'envoi d\'email depuis Smart Event'
    message = 'Ceci est un email de test pour vérifier que l\'envoi d\'emails fonctionne correctement.'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = ['yassinboulabiar13@gmail.com']  # Remplacez par votre email
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        print("✅ Email envoyé avec succès !")
        print(f"De: {from_email}")
        print(f"À: {', '.join(recipient_list)}")
        print(f"Sujet: {subject}")
    except Exception as e:
        print("❌ Erreur lors de l'envoi de l'email:")
        print(str(e))

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_event.settings')
    django.setup()
    
    # Afficher la configuration actuelle
    from django.conf import settings
    print("\n" + "="*70)
    print("CONFIGURATION EMAIL ACTUELLE")
    print("="*70)
    print(f"EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Non défini')}")
    print(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Non défini')}")
    print(f"EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Non défini')}")
    print(f"EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Non défini')}")
    print(f"EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'Non défini')}")
    print("="*70 + "\n")
    
    # Tester l'envoi d'email
    test_email_sending()
