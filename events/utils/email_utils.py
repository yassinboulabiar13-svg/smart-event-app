import logging
import qrcode
from io import BytesIO
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger('email_utils')

def generate_qr_code(url, size=10, border=4, fill_color="#4a6fa5"):
    """
    Génère un QR code à partir d'une URL
    """
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size,
            border=border,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color=fill_color, back_color="white")
        
        buffer = BytesIO()
        qr_img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return buffer
    except Exception as e:
        logger.error(f"Erreur lors de la génération du QR code: {str(e)}")
        return None

def send_private_event_invitation(event, guest_email, rsvp_url, request=None):
    """
    Envoie une invitation par email pour un événement privé avec QR code
    """
    try:
        # Préparer le contexte pour le template
        context = {
            'event': event,
            'rsvp_url': rsvp_url,
            'site_name': 'Smart Event',
            'current_year': timezone.now().year
        }
        
        # Rendre le contenu HTML
        html_content = render_to_string('emails/private_event_invitation.html', context)
        
        # Créer le message texte brut
        text_content = f"""
        🎉 Invitation à l'événement : {event.title}
        {'=' * 50}
        
        Bonjour,
        
        Vous avez été invité(e) à participer à l'événement :
        📌 {event.title}
        
        📅 Date : {event.date.strftime('%A %d %B %Y à %H:%M')}
        📍 Lieu : {event.location}
        
        🔗 Lien de confirmation :
        {rsvp_url}
        
        Scannez le QR code ci-joint pour accéder rapidement à la page de confirmation.
        
        Cordialement,
        L'équipe Smart Event
        """
        
        # Générer le QR code
        qr_buffer = generate_qr_code(rsvp_url)
        
        if qr_buffer is None:
            logger.error("Impossible de générer le QR code, l'email sera envoyé sans QR code")
        
        # Créer l'email
        subject = f"🎉 Invitation : {event.title}"
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[guest_email],
            reply_to=[event.owner.email]  # Permettre de répondre à l'organisateur
        )
        
        # Ajouter la version HTML
        email.attach_alternative(html_content, "text/html")
        
        # Ajouter le QR code en pièce jointe inline si disponible
        if qr_buffer:
            try:
                from email.mime.image import MIMEImage
                
                # Créer une pièce jointe MIME pour l'image
                mime_image = MIMEImage(qr_buffer.getvalue())
                mime_image.add_header('Content-ID', '<qrcode>')
                mime_image.add_header('Content-Disposition', 'inline', filename='qrcode.png')
                
                # Attacher l'image au message
                email.attach(mime_image)
                logger.info("QR code ajouté avec succès à l'email")
            except Exception as e:
                logger.error(f"Erreur lors de l'ajout du QR code: {str(e)}")
        
        # Envoyer l'email
        email_sent = email.send(fail_silently=False)
        
        if email_sent == 1:
            logger.info(f"✅ Email d'invitation envoyé avec succès à {guest_email}")
            return True
        else:
            logger.error(f"❌ Échec de l'envoi de l'email à {guest_email}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'envoi de l'email à {guest_email}: {str(e)}", exc_info=True)
        return False


def send_rsvp_confirmation(guest, event, response):
    """
    Envoie une confirmation de réponse à une invitation par email
    """
    try:
        # Déterminer le statut de la réponse
        status_display = "acceptée" if response == "accepted" else "déclinée"
        
        # Préparer le contexte pour le template
        context = {
            'event': event,
            'status_display': status_display,
            'guest': guest,
            'site_name': 'Smart Event',
            'current_year': timezone.now().year
        }
        
        # Rendre le contenu HTML
        html_content = render_to_string('emails/rsvp_confirmation.html', context)
        
        # Créer le message texte brut
        text_content = f"""
        Confirmation de votre réponse - {event.title}
        
        Bonjour,
        
        Nous vous confirmons que votre réponse à l'invitation pour l'événement "{event.title}" a bien été enregistrée.
        
        Votre réponse : {status_display}
        
        Détails de l'événement :
        📅 Date : {event.date.strftime('%A %d %B %Y à %H:%M')}
        📍 Lieu : {event.location}
        
        Merci pour votre réponse !
        
        Cordialement,
        L'équipe Smart Event
        """
        
        # Créer l'email
        subject = f"✅ Confirmation - Votre réponse pour : {event.title}"
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[guest.email],
            reply_to=[event.owner.email]  # Permettre de répondre à l'organisateur
        )
        
        # Ajouter la version HTML
        email.attach_alternative(html_content, "text/html")
        
        # Envoyer l'email
        email_sent = email.send(fail_silently=False)
        
        if email_sent == 1:
            logger.info(f"Email de confirmation RSVP envoyé avec succès à {guest.email} pour l'événement {event.id}")
            return True
        else:
            logger.error(f"Échec de l'envoi de l'email de confirmation RSVP à {guest.email}")
            return False
            
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email de confirmation RSVP à {guest.email}: {str(e)}", exc_info=True)
        return False
