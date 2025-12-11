from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import PrivateEvent, PublicEvent, Guest, UserProfile, ContactMessage, TwoFactorAuth

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Adresse email")

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email


class PrivateEventForm(forms.ModelForm):
    guests_emails = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'ex: alice@gmail.com, bob@yahoo.fr',
            'class': 'form-control-dark'
        }),
        help_text="Emails séparés par des virgules"
    )

    class Meta:
        model = PrivateEvent
        fields = ['title', 'description', 'date', 'location', 'online_link', 'image', 'guests_emails']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control-dark', 'placeholder': 'Titre de votre événement privé'}),
            'description': forms.Textarea(attrs={'class': 'form-control-dark', 'rows': 4, 'placeholder': 'Description...'}),
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control-dark'}),
            'location': forms.TextInput(attrs={'class': 'form-control-dark', 'placeholder': 'Lieu ou adresse'}),
            'online_link': forms.URLInput(attrs={'class': 'form-control-dark', 'placeholder': 'https://...'}),
            'image': forms.FileInput(attrs={'class': 'form-control-dark', 'accept': 'image/*'}),
        }
        help_texts = {'image': 'Image de couverture pour votre événement (recommandé)'}

    def clean_guests_emails(self):
        emails_str = self.cleaned_data.get('guests_emails', '')
        emails = [email.strip() for email in emails_str.split(',') if email.strip()]
        invalid_emails = []
        for e in emails:
            try:
                validate_email(e)
            except ValidationError:
                invalid_emails.append(e)
        if invalid_emails:
            raise forms.ValidationError(f"Emails invalides : {', '.join(invalid_emails)}")
        return ', '.join(emails)

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date < timezone.now():
            raise forms.ValidationError("La date de l'événement ne peut pas être dans le passé.")
        return date

from django import forms
from django.utils import timezone
from .models import PublicEvent

class PublicEventForm(forms.ModelForm):

    IS_PAID_CHOICES = [
        ('free', '🎫 Événement Gratuit'),
        ('paid', '💰 Événement Payant'),
    ]

    # ⚠️ Ce champ n’est PAS un BooleanField → donc il donne "free" ou "paid"
    is_paid = forms.ChoiceField(
        choices=IS_PAID_CHOICES,
        required=True,
        initial='free',
        label="Type d'événement",
        widget=forms.Select(attrs={
            'class': 'form-select-dark',
            'id': 'is-paid-select'
        })
    )

    price = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        min_value=0,
        label="Prix (DT)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control-dark', 
            'placeholder': '0.00', 
            'step': '0.01',
            'id': 'price-input'
        })
    )

    max_participants = forms.IntegerField(
        required=False,
        min_value=1,
        label="Nombre maximum de participants",
        widget=forms.NumberInput(attrs={
            'class': 'form-control-dark', 
            'placeholder': 'Laisser vide pour illimité'
        })
    )

    class Meta:
        model = PublicEvent
        fields = [
            'title', 'description', 'date', 'location', 
            'online_link', 'image', 'is_paid', 'price', 'max_participants'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control-dark', 
                'placeholder': 'Titre de votre événement'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control-dark', 
                'rows': 4,
                'placeholder': 'Description détaillée de votre événement...'
            }),
            'date': forms.DateTimeInput(attrs={
                'type': 'datetime-local', 
                'class': 'form-control-dark'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control-dark',
                'placeholder': 'Lieu physique de l\'événement'
            }),
            'online_link': forms.URLInput(attrs={
                'class': 'form-control-dark',
                'placeholder': 'https://... (optionnel)'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control-dark', 
                'accept': 'image/*'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Pré-remplissage lors de l'édition
        if self.instance and self.instance.pk:
            if self.instance.is_paid:
                self.fields['is_paid'].initial = 'paid'
                self.fields['price'].initial = self.instance.price
            else:
                self.fields['is_paid'].initial = 'free'
                self.fields['price'].initial = None

    # 🔥🔥🔥 La correction IMPORTANTE : convertir "paid"/"free" → True/False
    def clean(self):
        cleaned_data = super().clean()
        choice = cleaned_data.get('is_paid')
        price = cleaned_data.get('price')

        if choice == 'paid':
            cleaned_data['is_paid'] = True
            if price is None or price <= 0:
                self.add_error('price', "Le prix doit être supérieur à 0 pour un événement payant.")
        else:
            cleaned_data['is_paid'] = False
            cleaned_data['price'] = None  # Pas de prix pour gratuit

        return cleaned_data

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date < timezone.now():
            raise forms.ValidationError("La date de l'événement ne peut pas être dans le passé.")
        return date

    def save(self, commit=True):
        instance = super().save(commit=False)

        # ⚠️ "is_paid" est maintenant vraiment un boolean
        instance.is_paid = self.cleaned_data["is_paid"]

        if not instance.is_paid:
            instance.price = None

        if commit:
            instance.save()

        return instance


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control-dark'}),
            'email': forms.EmailInput(attrs={'class': 'form-control-dark'})
        }


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'bio', 'profile_picture']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control-dark', 
                'placeholder': '+33 1 23 45 67 89'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control-dark', 
                'rows': 4,
                'placeholder': 'Parlez-nous un peu de vous...'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control-dark', 
                'accept': 'image/*'
            }),
        }
        labels = {
            'phone': 'Téléphone',
            'bio': 'Biographie',
            'profile_picture': 'Photo de profil',
        }


class ProfileUpdateCombinedForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control-dark'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control-dark'})
    )

    class Meta:
        model = UserProfile
        fields = ['phone', 'bio', 'profile_picture']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control-dark',
                'placeholder': '+33 1 23 45 67 89'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control-dark', 
                'rows': 4,
                'placeholder': 'Parlez-nous un peu de vous...'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control-dark',
                'accept': 'image/*'
            }),
        }
        labels = {
            'phone': 'Téléphone',
            'bio': 'Biographie',
            'profile_picture': 'Photo de profil',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if (self.instance and self.instance.user and 
            User.objects.exclude(pk=self.instance.user.pk).filter(username=username).exists()):
            raise forms.ValidationError("Ce nom d'utilisateur est déjà utilisé.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if (self.instance and self.instance.user and 
            User.objects.exclude(pk=self.instance.user.pk).filter(email=email).exists()):
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.instance and self.instance.user:
            self.instance.user.username = self.cleaned_data['username']
            self.instance.user.email = self.cleaned_data['email']
            if commit:
                self.instance.user.save()
                profile.save()
        return profile


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control-dark', 
                'placeholder': 'Votre nom complet'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control-dark', 
                'placeholder': 'votre@email.com'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control-dark', 
                'rows': 5, 
                'placeholder': 'Votre message...'
            }),
        }
        labels = {
            'name': 'Nom complet',
            'email': 'Adresse email',
            'message': 'Message',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            validate_email(email)
        except ValidationError:
            raise forms.ValidationError("Veuillez entrer une adresse email valide.")
        return email


class MockPaymentForm(forms.Form):
    card_number = forms.CharField(
        max_length=19, 
        required=True, 
        label="Numéro de carte",
        widget=forms.TextInput(attrs={
            'class': 'form-control-dark', 
            'placeholder': '1234 5678 9012 3456', 
            'pattern': '[0-9\\s]{13,19}',
            'title': '13 à 19 chiffres (espaces autorisés)'
        })
    )
    expiry_date = forms.CharField(
        max_length=7, 
        required=True, 
        label="Date d'expiration (MM/AA)",
        widget=forms.TextInput(attrs={
            'class': 'form-control-dark', 
            'placeholder': '12/25', 
            'pattern': '(0[1-9]|1[0-2])/[0-9]{2}',
            'title': 'Format: MM/AA'
        })
    )
    cvv = forms.CharField(
        max_length=4, 
        required=True, 
        label="CVV",
        widget=forms.TextInput(attrs={
            'class': 'form-control-dark', 
            'placeholder': '123', 
            'type': 'password', 
            'pattern': '[0-9]{3,4}',
            'title': '3 ou 4 chiffres',
            'maxlength': '4'
        })
    )
    card_holder = forms.CharField(
        max_length=100,
        required=True,
        label="Titulaire de la carte",
        widget=forms.TextInput(attrs={
            'class': 'form-control-dark',
            'placeholder': 'NOM PRENOM'
        })
    )
    amount = forms.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        required=True, 
        label="Montant (DT)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control-dark', 
            'readonly': 'readonly', 
            'step': '0.01'
        })
    )

    def clean_card_number(self):
        card_number = self.cleaned_data['card_number'].replace(' ', '')
        if not card_number.isdigit() or len(card_number) not in [13, 14, 15, 16]:
            raise forms.ValidationError("Numéro de carte invalide. Doit contenir entre 13 et 16 chiffres.")
        return card_number

    def clean_expiry_date(self):
        expiry_date = self.cleaned_data['expiry_date']
        try:
            month, year = expiry_date.split('/')
            month = int(month)
            year = int(year)
            if not (1 <= month <= 12):
                raise forms.ValidationError("Le mois doit être entre 01 et 12.")
            
            # Vérifier si la carte n'a pas expiré
            current_year = timezone.now().year % 100
            current_month = timezone.now().month
            if year < current_year or (year == current_year and month < current_month):
                raise forms.ValidationError("La carte a expiré.")
        except ValueError:
            raise forms.ValidationError("Format invalide. Utilisez MM/AA (ex: 12/25).")
        return expiry_date

    def clean_cvv(self):
        cvv = self.cleaned_data['cvv']
        if not cvv.isdigit() or len(cvv) not in [3, 4]:
            raise forms.ValidationError("CVV invalide. Doit contenir 3 ou 4 chiffres.")
        return cvv

    def clean_card_holder(self):
        card_holder = self.cleaned_data['card_holder'].strip()
        if len(card_holder) < 2:
            raise forms.ValidationError("Veuillez entrer le nom complet du titulaire de la carte.")
        return card_holder.upper()


class EventSearchForm(forms.Form):
    query = forms.CharField(
        required=False, 
        label="",
        widget=forms.TextInput(attrs={
            'placeholder': 'Rechercher un événement...', 
            'class': 'form-control-dark'
        })
    )
    event_type = forms.ChoiceField(
        choices=[
            ('all', 'Tous les événements'), 
            ('public', 'Événements publics'), 
            ('private', 'Événements privés')
        ],
        required=False, 
        initial='all', 
        widget=forms.Select(attrs={'class': 'form-select-dark'})
    )
    date_filter = forms.ChoiceField(
        choices=[
            ('all', 'Toutes les dates'),
            ('today', "Aujourd'hui"),
            ('week', 'Cette semaine'),
            ('month', 'Ce mois'),
            ('upcoming', 'À venir'),
        ],
        required=False,
        initial='all',
        label="Filtrer par date",
        widget=forms.Select(attrs={'class': 'form-select-dark'})
    )


class EventFilterForm(forms.Form):
    EVENT_TYPE_CHOICES = [
        ('', 'Tous les types'),
        ('public', 'Événements publics'),
        ('private', 'Événements privés'),
    ]
    
    PRICE_CHOICES = [
        ('', 'Tous les prix'),
        ('free', 'Gratuits seulement'),
        ('paid', 'Payants seulement'),
    ]
    
    event_type = forms.ChoiceField(
        choices=EVENT_TYPE_CHOICES,
        required=False,
        label="Type d'événement",
        widget=forms.Select(attrs={'class': 'form-select-dark'})
    )
    
    price_type = forms.ChoiceField(
        choices=PRICE_CHOICES,
        required=False,
        label="Type de prix",
        widget=forms.Select(attrs={'class': 'form-select-dark'})
    )
    
    date_from = forms.DateField(
        required=False,
        label="À partir du",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control-dark'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        label="Jusqu'au",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control-dark'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to:
            if date_from > date_to:
                self.add_error('date_to', "La date de fin ne peut pas être avant la date de début.")
        
        return cleaned_data


class GuestResponseForm(forms.Form):
    RESPONSE_CHOICES = [
        ('accepted', "✅ J'accepte l'invitation"),
        ('declined', "❌ Je décline l'invitation"),
    ]
    
    response = forms.ChoiceField(
        choices=RESPONSE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Votre réponse"
    )
    
    message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control-dark',
            'rows': 3,
            'placeholder': 'Message optionnel pour l\'organisateur...'
        }),
        label="Message (optionnel)"
    )


class TwoFactorVerificationForm(forms.Form):
    """Formulaire pour la vérification du code 2FA"""
    code = forms.CharField(
        max_length=6,
        min_length=6,
        required=True,
        label="Code de vérification",
        widget=forms.TextInput(attrs={
            'class': 'form-control-lg text-center',
            'placeholder': '123456',
            'autofocus': True,
            'inputmode': 'numeric',
            'pattern': '\d{6}',
            'title': 'Veuillez entrer un code à 6 chiffres',
            'autocomplete': 'one-time-code',
            'style': 'letter-spacing: 0.5em; font-size: 1.5rem;',
        })
    )
    
    def clean_code(self):
        code = self.cleaned_data.get('code')
        if not code.isdigit() or len(code) != 6:
            raise forms.ValidationError("Le code doit contenir exactement 6 chiffres.")
        return code


class Toggle2FAForm(forms.Form):
    """Formulaire pour activer/désactiver la 2FA"""
    enable_2fa = forms.BooleanField(
        required=False,
        label="Activer l'authentification à deux facteurs",
        help_text="Ajoutez une couche de sécurité supplémentaire à votre compte en exigeant un code de vérification à chaque connexion.",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'data-bs-toggle': 'toggle',
            'data-on': 'Activée',
            'data-off': 'Désactivée',
            'data-onstyle': 'success',
            'data-offstyle': 'secondary',
        })
    )


class CustomAuthenticationForm(AuthenticationForm):
    """Formulaire de connexion personnalisé avec support 2FA"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control-dark',
            'placeholder': 'Nom d\'utilisateur ou email',
            'autofocus': True
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control-dark',
            'placeholder': 'Mot de passe'
        })
    
    def confirm_login_allowed(self, user):
        """Vérifie si l'utilisateur peut se connecter"""
        super().confirm_login_allowed(user)
        
        # Vérifier si la 2FA est activée pour cet utilisateur
        try:
            two_fa = user.two_factor_auth
            if two_fa.is_enabled:
                # Stocker l'ID utilisateur dans la session pour la vérification 2FA
                self.request.session['2fa_user_id'] = user.id
        except TwoFactorAuth.DoesNotExist:
            pass