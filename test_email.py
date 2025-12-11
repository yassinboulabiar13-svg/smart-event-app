import os
import sys
import django
from pathlib import Path

# Configuration de l'environnement Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'False') == 'True'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'True') == 'True'  # Utilisation de SSL pour le port 465
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_event.settings')
django.setup()

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import qrcode
from io import BytesIO

def send_test_email():
    # Générer un QR code de test
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data('https://example.com/rsvp/test-token/')
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color='#4a6fa5', back_color='white')
    buffer = BytesIO()
    qr_img.save(buffer, format='PNG')
    buffer.seek(0)
    
    # Préparer le contenu de l'email
    subject = "🎉 Test d'envoi d'email avec QR code"
    text_content = 'Ceci est un email de test avec un QR code.'
    html_content = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test d'envoi d'email</title>
        <style>
            body { font-family: Arial, sans-serif; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .qr-code { text-align: center; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Test d'envoi d'email avec QR code</h2>
            <p>Ceci est un email de test avec un QR code intégré.</p>
            <div class="qr-code">
                <img src="cid:qrcode" alt="QR Code">
                <p>Scannez ce QR code pour tester</p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    # Créer l'email
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=['yassinboulabiar13@gmail.com'],
        reply_to=['yassinboulabiar13@gmail.com']
    )
    
    # Ajouter la version HTML
    email.attach_alternative(html_content, 'text/html')
    
    # Ajouter le QR code
    from email.mime.image import MIMEImage
    mime_image = MIMEImage(buffer.read())
    mime_image.add_header('Content-ID', '<qrcode>')
    mime_image.add_header('Content-Disposition', 'inline', filename='qrcode.png')
    email.attach(mime_image)
    
    # Envoyer l'email
    try:
        email.send(fail_silently=False)
        print('✅ Email de test envoyé avec succès !')
        print('Veuillez vérifier votre boîte de réception et les spams.')
    except Exception as e:
        print('Erreur lors de l\'envoi de l\'email :')
        print(str(e))

if __name__ == '__main__':
    send_test_email()