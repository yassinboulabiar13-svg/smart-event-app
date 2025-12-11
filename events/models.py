from django.db import models
from django.contrib.auth.models import User
import uuid
import random
import string
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

# ==========================================================
# 🔐 MODÈLE POUR L'AUTHENTIFICATION 2FA
# ==========================================================
class TwoFactorAuth(models.Model):
    """
    Modèle pour gérer l'authentification à deux facteurs par email
    Activée par défaut pour tous les utilisateurs
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='two_factor_auth')
    is_enabled = models.BooleanField(default=True, verbose_name="2FA activée")
    last_verified = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def generate_code(self):
        """Génère un code de vérification à 6 chiffres"""
        return ''.join(random.choices(string.digits, k=6))

    def send_verification_email(self, request=None):
        """Envoie un email avec le code de vérification"""
        if not self.is_enabled:
            print("DEBUG: 2FA non activée pour cet utilisateur")
            return False
            
        try:
            # Générer un nouveau code
            verification_code = self.generate_code()
            print(f"DEBUG: Génération du code: {verification_code}")
            
            # Créer ou mettre à jour le code de vérification
            TwoFactorCode.objects.filter(user=self.user).delete()
            code = TwoFactorCode.objects.create(
                user=self.user,
                code=verification_code,
                expires_at=timezone.now() + timezone.timedelta(minutes=15)
            )
            print(f"DEBUG: Code enregistré: {code}")
            
            # Envoyer l'email
            subject = 'Votre code de vérification à deux facteurs'
            message = f'Votre code de vérification est : {verification_code}\n\nCe code est valable 15 minutes.'
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [self.user.email]
            
            print(f"DEBUG: Envoi de l'email à {recipient_list}")
            print(f"DEBUG: De: {from_email}")
            print(f"DEBUG: Sujet: {subject}")
            print(f"DEBUG: Message: {message}")
            
            try:
                send_mail(
                    subject,
                    message,
                    from_email,
                    recipient_list,
                    fail_silently=False,
                )
                print("DEBUG: Email envoyé avec succès")
                return True
            except Exception as e:
                print(f"ERREUR lors de l'envoi de l'email: {str(e)}")
                return False
        except Exception as e:
            print(f"ERREUR dans send_verification_email: {str(e)}")
            return False

    def verify_code(self, code):
        """Vérifie si le code fourni est valide"""
        try:
            verification_code = TwoFactorCode.objects.get(
                user=self.user,
                code=code,
                expires_at__gt=timezone.now(),
                is_used=False
            )
            verification_code.is_used = True
            verification_code.save()
            self.last_verified = timezone.now()
            self.save()
            return True
        except TwoFactorCode.DoesNotExist:
            return False


class TwoFactorCode(models.Model):
    """Modèle pour stocker les codes de vérification 2FA"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_codes')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.code}"


# ==========================================================
# 🧍‍♂️ PROFIL UTILISATEUR
# ==========================================================
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)

    def __str__(self):
        return self.user.username


# ==========================================================
# 📅 MODÈLE DE BASE DES ÉVÉNEMENTS
# ==========================================================
class BaseEvent(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateTimeField()
    location = models.CharField(max_length=200)
    online_link = models.URLField(blank=True, null=True)
    # ✅ NOUVEAU : Champ image pour tous les événements
    image = models.ImageField(
        upload_to='events/images/',
        blank=True,
        null=True,
        help_text="Image de couverture de l'événement"
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.title

    # 🔹 Pratique dans les templates
    @property
    def event_type(self):
        """Retourne 'public' ou 'private' selon le type de l'événement."""
        if isinstance(self, PublicEvent):
            return 'public'
        elif isinstance(self, PrivateEvent):
            return 'private'
        return ''

    @property
    def is_past(self):
        """Vérifie si l'événement est passé"""
        from django.utils import timezone
        return self.date < timezone.now()

    @property
    def guest_count(self):
        """Nombre d'invités acceptés"""
        return self.guests.filter(status=Guest.STATUS_ACCEPTED).count()


# ==========================================================
# 🔒 ÉVÉNEMENTS PRIVÉS
# ==========================================================
class PrivateEvent(BaseEvent):
    class Meta:
        verbose_name = "Événement privé"
        verbose_name_plural = "Événements privés"
        indexes = [
            models.Index(fields=['owner', 'date']),
            models.Index(fields=['date']),
        ]


# ==========================================================
# 🌍 ÉVÉNEMENTS PUBLICS
# ==========================================================
class PublicEvent(BaseEvent):
    # ✅ Champs spécifiques aux événements publics
    is_paid = models.BooleanField(default=False)
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        blank=True,
        null=True,
        help_text="Prix pour les événements payants"
    )
    max_participants = models.PositiveIntegerField(
        blank=True, 
        null=True,
        help_text="Nombre maximum de participants (laisser vide pour illimité)"
    )

    class Meta:
        verbose_name = "Événement public"
        verbose_name_plural = "Événements publics"
        indexes = [
            models.Index(fields=['owner', 'date']),
            models.Index(fields=['date']),
            models.Index(fields=['is_paid']),
        ]

    @property
    def is_full(self):
        """Vérifie si l'événement est complet"""
        if self.max_participants:
            return self.guest_count >= self.max_participants
        return False

    def __str__(self):
        paid_info = "💰 Payant" if self.is_paid else "🎫 Gratuit"
        return f"{self.title} - {self.date.strftime('%d/%m/%Y')} ({paid_info})"


# ==========================================================
# 👥 INVITÉS (GUESTS)
# ==========================================================
class Guest(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_DECLINED = 'declined'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'En attente'),
        (STATUS_ACCEPTED, 'Accepté'),
        (STATUS_DECLINED, 'Décliné'),
    ]

    event_private = models.ForeignKey(
        PrivateEvent,
        related_name='guests',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    event_public = models.ForeignKey(
        PublicEvent,
        related_name='guests',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    email = models.EmailField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    checked_in = models.BooleanField(default=False)

    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    payment_status = models.CharField(
        max_length=20,
        default='pending',
        choices=[
            ('pending', 'En attente'),
            ('paid', 'Payé'),
            ('failed', 'Échoué'),
            ('refunded', 'Remboursé'),
        ]
    )
    payment_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        event = self.event_private or self.event_public
        return f"{self.email} → {event.title} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Invité"
        verbose_name_plural = "Invités"
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(event_private__isnull=False, event_public__isnull=True) |
                    models.Q(event_private__isnull=True, event_public__isnull=False)
                ),
                name='guest_linked_to_one_event_type'
            )
        ]
        indexes = [
            models.Index(fields=['email', 'status']),
            models.Index(fields=['token']),
            models.Index(fields=['event_private', 'status']),
            models.Index(fields=['event_public', 'status']),
            models.Index(fields=['payment_status']),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        if not (self.event_private or self.event_public):
            raise ValidationError("Un invité doit être lié à un événement public ou privé")
        if self.event_private and self.event_public:
            raise ValidationError("Un invité ne peut être lié qu'à un seul type d'événement")

    @property
    def event(self):
        return self.event_private or self.event_public

    class Meta:
        verbose_name = "Invité"
        verbose_name_plural = "Invités"
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(event_private__isnull=False, event_public__isnull=True) |
                    models.Q(event_private__isnull=True, event_public__isnull=False)
                ),
                name='guest_linked_to_one_event_type'
            )
        ]
        indexes = [
            models.Index(fields=['email', 'status']),
            models.Index(fields=['token']),
            models.Index(fields=['event_private', 'status']),
            models.Index(fields=['event_public', 'status']),
            models.Index(fields=['payment_status']),
        ]

    def clean(self):
        """Validation pour s'assurer qu'un guest est lié à un seul événement"""
        from django.core.exceptions import ValidationError
        if not (self.event_private or self.event_public):
            raise ValidationError("Un invité doit être lié à un événement public ou privé")
        if self.event_private and self.event_public:
            raise ValidationError("Un invité ne peut être lié qu'à un seul type d'événement")

    @property
    def event(self):
        """Retourne l'événement associé (privé ou public)"""
        return self.event_private or self.event_public


# ==========================================================
# ✅ RSVP (Participation confirmée à un événement)
# ==========================================================
class RSVP(models.Model):
    """
    Représente la confirmation de participation d'un utilisateur
    à un événement public ou privé.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event_private = models.ForeignKey(
        PrivateEvent, on_delete=models.CASCADE, null=True, blank=True, related_name='rsvps'
    )
    event_public = models.ForeignKey(
        PublicEvent, on_delete=models.CASCADE, null=True, blank=True, related_name='rsvps'
    )
    response = models.CharField(
        max_length=10,
        choices=[('yes', 'Oui'), ('no', 'Non'), ('maybe', 'Peut-être')],
        default='yes'
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        event_name = self.event_private.title if self.event_private else self.event_public.title
        return f"{self.user.username} → {event_name} ({self.response})"

    class Meta:
        verbose_name = "RSVP (Participation)"
        verbose_name_plural = "RSVPs (Participations)"
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(event_private__isnull=False, event_public__isnull=True) |
                    models.Q(event_private__isnull=True, event_public__isnull=False)
                ),
                name='rsvp_linked_to_one_event_type'
            )
        ]


# ==========================================================
# ✉️ MESSAGES DE CONTACT
# ==========================================================
class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message de {self.name} ({self.email})"

    class Meta:
        verbose_name = "Message de contact"
        verbose_name_plural = "Messages de contact"
        ordering = ['-created_at']