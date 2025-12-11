from decimal import Decimal, InvalidOperation
import json
import qrcode
import qrcode.image.svg
from io import BytesIO
from django.core.files import File
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives, BadHeaderError
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.utils.timezone import localtime, now
from django.db.models import Q, Count, Sum, F, ExpressionWrapper, fields
from django.db.models.functions import TruncDate, TruncMonth, TruncYear
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from decimal import Decimal

# Récupérer le modèle User personnalisé
User = get_user_model()

from .models import PrivateEvent, PublicEvent, Guest, UserProfile, ContactMessage, RSVP, User
from .forms import (
    PrivateEventForm,
    PublicEventForm,
    CustomUserCreationForm,
    ProfileUpdateForm,
    UserUpdateForm,
    ContactForm,
    MockPaymentForm
)
from .forms import UserUpdateForm, ProfileUpdateForm  # Ajout des imports manquants

# ================================
# Public Pages
# ================================

def home(request):
    """
    Vue pour la page d'accueil du site
    """
    query = request.GET.get('q', '')
    
    # Récupérer les événements publics (tous pour le moment)
    events = PublicEvent.objects.all().order_by('date')
    
    # Appliquer la recherche si un terme est fourni
    if query:
        events = events.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query)
        )
    
    # Limiter à 6 événements pour l'affichage
    events = events[:6]
    
    # Ajouter un message de débogage
    print(f"Événements trouvés : {events.count()}")
    for event in events:
        print(f"- {event.title} ({event.date})")
    
    context = {
        'events': events,
        'query': query
    }
    
    return render(request, 'events/home.html', context)

def about(request):
    """
    Vue pour la page À propos
    """
    return render(request, 'events/about.html')

def contact(request):
    """
    Vue pour la page de contact
    """
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Créer un nouveau message de contact
            contact_message = ContactMessage(
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                subject=form.cleaned_data['subject'],
                message=form.cleaned_data['message']
            )
            contact_message.save()
            
            # Envoyer un email (optionnel)
            try:
                send_mail(
                    f"Nouveau message de contact: {form.cleaned_data['subject']}",
                    f"De: {form.cleaned_data['name']} <{form.cleaned_data['email']}>\n\n{form.cleaned_data['message']}",
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.DEFAULT_FROM_EMAIL],
                    fail_silently=False,
                )
            except Exception as e:
                # En cas d'erreur d'envoi d'email, on continue quand même
                pass
            
            messages.success(request, 'Votre message a été envoyé avec succès !')
            return redirect('contact')
    else:
        if request.user.is_authenticated:
            form = ContactForm(initial={
                'name': request.user.get_full_name() or request.user.username,
                'email': request.user.email
            })
        else:
            form = ContactForm()
    
    return render(request, 'events/contact.html', {'form': form})

def public_events(request):
    """
    Vue pour afficher la liste des événements publics
    """
    # Récupérer les paramètres de filtrage
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    
    # Filtrer les événements publics à venir
    events = PublicEvent.objects.filter(date__gte=timezone.now())
    
    # Appliquer les filtres
    if query:
        events = events.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(location__icontains=query)
        )
    
    if category:
        events = events.filter(category=category)
    
    # Trier par date
    events = events.order_by('date')
    
    # Préparer le contexte
    context = {
        'events': events,
        'query': query,
        'category': category,
        'now': timezone.now(),
    }
    
    return render(request, 'events/public_events.html', context)

@login_required
def private_events(request):
    """
    Vue pour afficher la liste des événements privés de l'utilisateur connecté
    """
    user = request.user
    
    # Récupérer les événements privés où l'utilisateur est propriétaire ou invité
    owned_events = PrivateEvent.objects.filter(owner=user).order_by('date')
    
    # Récupérer les événements où l'utilisateur est invité
    invited_events = PrivateEvent.objects.filter(
        guests__email__iexact=user.email
    ).exclude(owner=user).distinct().order_by('date')
    
    # Récupérer le statut de chaque événement pour l'utilisateur
    event_status = {}
    for event in invited_events:
        try:
            guest = Guest.objects.get(event_private=event, email__iexact=user.email)
            event_status[event.id] = {
                'status': guest.get_status_display(),
                'status_class': 'text-warning' if guest.status == 'pending' else 
                              'text-success' if guest.status == 'accepted' else 
                              'text-danger'
            }
        except Guest.DoesNotExist:
            event_status[event.id] = {'status': 'Invité', 'status_class': 'text-muted'}
    
    # Récupérer les paramètres de filtrage
    query = request.GET.get('q', '')
    event_type = request.GET.get('type', 'all')  # 'all', 'owned', 'invited'
    
    # Filtrer les événements selon le type sélectionné
    if event_type == 'owned':
        events = owned_events
    elif event_type == 'invited':
        events = invited_events
    else:  # 'all'
        events = list(owned_events) + list(invited_events)
    
    # Appliquer le filtre de recherche
    if query:
        events = [
            event for event in events 
            if (query.lower() in event.title.lower() or 
                query.lower() in event.location.lower() or
                query.lower() in event.description.lower())
        ]
    
    # Trier les événements par date
    events = sorted(events, key=lambda x: x.date)
    
    # Préparer le contexte
    context = {
        'owned_events': owned_events,
        'invited_events': invited_events,
        'events': events,
        'event_status': event_status,
        'query': query,
        'event_type': event_type,
        'now': timezone.now(),
    }
    
    return render(request, 'events/private_events.html', context)

# ================================
# Auth & Registration
# ================================

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.save()
            login(request, user)
            messages.success(request, f"Bienvenue {user.username} 🎉")
            return redirect('event_detail', event_type='private', event_id=event.id)
        else:
            messages.error(request, "Erreur dans le formulaire d'inscription.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'events/register.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# ================================
# Dashboard
# ================================

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now, localtime
from .models import PrivateEvent, PublicEvent, Guest, RSVP

from django.contrib.auth.decorators import login_required
from django.utils.timezone import localtime, now
from django.shortcuts import render
from .models import PrivateEvent, PublicEvent, Guest

@login_required
def dashboard(request):
    user = request.user
    user_email = user.email.strip().lower() if user.email else None
    event_type = request.GET.get('type', 'all')

    # Événements privés
    private_created = PrivateEvent.objects.filter(owner=user)
    private_pending = PrivateEvent.objects.filter(
        guests__email__iexact=user_email, guests__status=Guest.STATUS_PENDING
    )
    private_attending = PrivateEvent.objects.filter(
        guests__email__iexact=user_email, guests__status=Guest.STATUS_ACCEPTED
    )
    private_declined = PrivateEvent.objects.filter(
        guests__email__iexact=user_email, guests__status=Guest.STATUS_DECLINED
    )

    # Événements publics
    public_created = PublicEvent.objects.filter(owner=user)
    public_pending = PublicEvent.objects.none()

    # Par RSVP : utilisateurs ayant répondu 'yes'
    public_attending_rsvp = PublicEvent.objects.filter(
        rsvps__user=user, rsvps__response='yes'
    ).distinct()

    # Par paiement : utilisateurs qui ont payé et statut accepté
    public_attending_payment = PublicEvent.objects.filter(
        guests__email__iexact=user_email, guests__payment_status='paid'
    ).distinct()

    # Combine RSVP et paiements pour "accepté", supprime doublons
    public_attending = list(dict.fromkeys(list(public_attending_rsvp) + list(public_attending_payment)))

    public_declined = PublicEvent.objects.none()

    # Filtrage selon le type choisi
    if event_type == 'private':
        created_events = private_created
        pending_events = private_pending
        attending_events = private_attending
        declined_events = private_declined
    elif event_type == 'public':
        created_events = public_created
        pending_events = public_pending
        attending_events = public_attending
        declined_events = public_declined
    else:  # all
        created_events = list(private_created) + list(public_created)
        pending_events = private_pending
        attending_events = list(private_attending) + public_attending
        declined_events = private_declined

    # Mapping des tokens pour RSVP ou Guest
    guest_tokens = {}
    if user_email:
        for g in Guest.objects.filter(email__iexact=user_email):
            if g.event_private:
                guest_tokens[g.event_private.id] = g.token
            elif g.event_public:
                guest_tokens[g.event_public.id] = g.token

    context = {
        'created_events': created_events,
        'pending_events': pending_events,
        'attending_events': attending_events,
        'declined_events': declined_events,
        'guest_tokens': guest_tokens,
        'event_type': event_type,
        'now': localtime(now()),
    }

    return render(request, 'events/dashboard.html', context)


# ================================
# Event CRUD
# ================================

@login_required
def add_public_event(request):
    if request.method == 'POST':
        form = PublicEventForm(request.POST, request.FILES)
        if form.is_valid():
            # Le form.clean() convertit déjà 'is_paid' en boolean et gère 'price'.
            event = form.save(commit=False)
            event.owner = request.user
            # Sauvegarder l'événement tel que préparé par le form
            event.save()
            
            messages.success(request, "L'événement public a été créé avec succès !")
            return redirect('dashboard')  # Redirection vers le tableau de bord après création
    else:
        form = PublicEventForm()
    
    return render(request, 'events/add_public_event.html', {'form': form})


@login_required
def add_private_event(request):
    """
    Vue pour ajouter un nouvel événement privé avec envoi d'invitations par email
    """
    if request.method == 'POST':
        form = PrivateEventForm(request.POST, request.FILES)
        if form.is_valid():
            # Sauvegarder l'événement
            event = form.save(commit=False)
            event.owner = request.user
            event.save()
            
            # Récupérer et nettoyer la liste des emails
            emails_str = form.cleaned_data.get('guests_emails', '')
            emails = [e.strip() for e in emails_str.split(',') if e.strip()]
            
            # Configuration du logger
            import logging
            logger = logging.getLogger('email_utils')
            
            log_context = {
                'event_id': event.id,
                'event_title': event.title,
                'guest_count': len(emails),
                'emails': emails
            }
            
            logger.info("Début de l'envoi des invitations", extra=log_context)
            
            # Importer l'utilitaire d'email
            from .utils.email_utils import send_private_event_invitation
            
            try:
                sent_count = 0
                failed_emails = []
                
                for email in emails:
                    try:
                        # Créer l'invité dans la base de données
                        guest = Guest.objects.create(event_private=event, email=email)
                        rsvp_link = f"{request.scheme}://{request.get_host()}/rsvp/{guest.token}/"
                        
                        # Envoyer l'invitation par email
                        email_sent = send_private_event_invitation(
                            event=event,
                            guest_email=email,
                            rsvp_url=rsvp_link,  
                            request=request
                        )
                        
                        if email_sent:
                            sent_count += 1
                            logger.info(f"Email envoyé avec succès à {email}", extra={
                                'email': email,
                                'event_id': event.id,
                                'rsvp_link': rsvp_link
                            })
                            
                            # Afficher un message de débogage en console
                            print(f"\n" + "="*50)
                            print(f"EMAIL ENVOYÉ AVEC SUCCÈS À: {email}")
                            print(f"Événement: {event.title}")
                            print(f"Lien RSVP: {rsvp_link}")
                            print("="*50 + "\n")
                        else:
                            failed_emails.append(email)
                            logger.warning(f"Échec d'envoi à {email}", extra={
                                'email': email,
                                'event_id': event.id
                            })
                            
                    except Exception as e:
                        import traceback
                        error_details = traceback.format_exc()
                        failed_emails.append(email)
                        logger.error(
                            f"Erreur lors de l'envoi à {email}", 
                            exc_info=True,
                            extra={
                                'email': email,
                                'error': str(e),
                                'event_id': event.id,
                                'traceback': error_details
                            }
                        )
                        
                        # Afficher un message d'erreur en console
                        print(f"\n" + "!"*50)
                        print(f"ERREUR D'ENVOI D'EMAIL À {email}")
                        print(f"Erreur: {str(e)}")
                        print("!"*50 + "\n")
                
                # Afficher les messages de statut à l'utilisateur
                if sent_count > 0:
                    messages.success(
                        request,
                        f"✅ Événement créé avec succès ! {sent_count} invitation(s) envoyée(s)."
                    )
                
                if failed_emails:
                    failed_count = len(failed_emails)
                    messages.warning(
                        request,
                        f"⚠️ {failed_count} invitation(s) n'ont pas pu être envoyées. "
                        f"Emails concernés : {', '.join(failed_emails[:5])}"
                        f"{'...' if len(failed_emails) > 5 else ''}"
                    )
                
            except Exception as e:
                logger.critical(
                    "Erreur critique lors de l'envoi des invitations", 
                    exc_info=True, 
                    extra=log_context
                )
                messages.error(
                    request,
                    "❌ Une erreur est survenue lors de l'envoi des invitations. "
                    "Veuillez réessayer ou contacter l'administrateur."
                )
                
                # Afficher l'erreur critique en console
                print("\n" + "!"*50)
                print("ERREUR CRITIQUE LORS DE L'ENVOI DES INVITATIONS")
                print(f"Erreur: {str(e)}")
                print("!"*50 + "\n")
                
            return redirect('dashboard')  # Redirection vers le tableau de bord après création
        else:
            # Afficher les erreurs de formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erreur dans le champ {field}: {error}")
    else:
        form = PrivateEventForm()
    
    return render(request, 'events/add_private_event.html', {'form': form})

# Event CRUD
# ================================

@login_required
def edit_public_event(request, event_id):
    event = get_object_or_404(PublicEvent, id=event_id)
    
    if request.user != event.owner:
        messages.error(request, "Vous n'êtes pas autorisé à modifier cet événement.")
        return redirect('event_detail', event_type='public', event_id=event.id)
        
    if request.method == "POST":
        form = PublicEventForm(request.POST, request.FILES, instance=event)

        if form.is_valid():
            # Let the form handle conversion and cleaned values
            updated_event = form.save(commit=False)
            updated_event.save()
            messages.success(request, "✅ Événement public mis à jour !")
            return redirect("dashboard")

        else:
            messages.error(request, "❌ Veuillez corriger les erreurs.")

    else:
        # Valeurs initiales cohérentes
        initial_data = {
            "is_paid": "paid" if event.is_paid else "free",
            "price": event.price if event.is_paid else "",
            "max_participants": event.max_participants,
        }

        form = PublicEventForm(instance=event, initial=initial_data)

    return render(
        request,
        "events/edit_public_event.html",
        {"form": form, "event": event},
    )


# ================================
# Admin Statistics
# ================================

@login_required
def admin_stats(request):
    # Vérifier si l'utilisateur est un superutilisateur
    if not request.user.is_superuser:
        messages.error(request, "Accès refusé. Vous n'avez pas les droits d'administrateur.")
        return redirect('event_detail', event_type='public', event_id=event.id)
    
    # Statistiques de base
    total_users = User.objects.count()
    total_events = PublicEvent.objects.count() + PrivateEvent.objects.count()
    public_events_count = PublicEvent.objects.count()
    private_events_count = PrivateEvent.objects.count()
    
    # Derniers événements créés
    recent_public_events = PublicEvent.objects.order_by('-created_at')[:5]
    recent_private_events = PrivateEvent.objects.order_by('-created_at')[:5]
    recent_events = list(recent_public_events) + list(recent_private_events)
    recent_events.sort(key=lambda x: x.created_at, reverse=True)
    
    # Préparation des données pour le graphique d'évolution mensuelle
    from django.db.models.functions import TruncMonth
    from django.db.models import Count
    
    # Événements publics par mois
    public_events_by_month = (
        PublicEvent.objects
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    
    # Événements privés par mois
    private_events_by_month = (
        PrivateEvent.objects
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    
    # Fusionner les données des événements publics et privés par mois
    from collections import defaultdict
    from datetime import datetime
    
    events_by_month = defaultdict(int)
    
    for event in public_events_by_month:
        month = event['month'].strftime('%Y-%m')
        events_by_month[month] += event['count']
    
    for event in private_events_by_month:
        month = event['month'].strftime('%Y-%m')
        events_by_month[month] += event['count']
    
    # Trier les mois et préparer les données pour le graphique
    sorted_months = sorted(events_by_month.keys())
    months = [datetime.strptime(month, '%Y-%m').strftime('%b %Y') for month in sorted_months]
    event_counts = [events_by_month[month] for month in sorted_months]
    
    # Préparer le contexte
    context = {
        'total_users': total_users,
        'total_events': total_events,
        'public_events_count': public_events_count,
        'private_events_count': private_events_count,
        'recent_events': recent_events[:5],  # Limiter à 5 événements récents
        'months': json.dumps(months, ensure_ascii=False),  # Convertir en JSON pour JavaScript
        'event_counts': json.dumps(event_counts),  # Convertir en JSON pour JavaScript
    }
    
    return render(request, 'events/admin_stats.html', context)


# ================================
# Event Detail & Join
# ================================

from decimal import Decimal, InvalidOperation
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .models import PublicEvent, PrivateEvent, Guest, RSVP
from .forms import MockPaymentForm

@login_required
def event_detail(request, event_type, event_id):
    now_time = timezone.localtime(timezone.now())

    # 🔹 Récupère l'événement
    if event_type == 'public':
        event = get_object_or_404(PublicEvent, id=event_id)
    elif event_type == 'private':
        event = get_object_or_404(PrivateEvent, id=event_id)
    else:
        messages.error(request, "Type d'événement invalide.")
        return redirect('event_detail', event_type='public', event_id=event.id)

    user_email = request.user.email.strip().lower() if request.user.email else None

    # 🔹 Vérifie si l'utilisateur a déjà rejoint l'événement
    if event_type == 'public':
        # Pour les événements publics payants, on vérifie le statut de paiement
        if event.is_paid and event.price is not None:
            user_has_joined = Guest.objects.filter(
                event_public=event,
                email__iexact=user_email,
                status=Guest.STATUS_ACCEPTED,
                payment_status='paid'
            ).exists()
        else:
            # Pour les événements publics gratuits, on vérifie soit Guest accepté, soit RSVP
            user_has_joined = Guest.objects.filter(
                event_public=event,
                email__iexact=user_email,
                status=Guest.STATUS_ACCEPTED
            ).exists() or RSVP.objects.filter(
                event_public=event,
                user=request.user,
                response='yes'
            ).exists()
    else:
        # Pour les événements privés
        user_has_joined = Guest.objects.filter(
            event_private=event,
            email__iexact=user_email,
            status=Guest.STATUS_ACCEPTED
        ).exists() or RSVP.objects.filter(
            event_private=event,
            user=request.user,
            response='yes'
        ).exists()

    # 🔹 Gestion des événements payants
    payment_form = None
    display_price = None
    has_paid = False
    
    if event_type == 'public' and event.is_paid and event.price is not None:
        display_price = f"{event.price:.2f}"
        
        # Vérifier si l'utilisateur a déjà payé
        has_paid = Guest.objects.filter(
            event_public=event,
            email__iexact=user_email,
            payment_status='paid',
            status=Guest.STATUS_ACCEPTED
        ).exists()
        
        # Initialiser le formulaire de paiement pour les événements payants
        if not has_paid and request.user.is_authenticated:
            if request.method == "POST":
                payment_form = MockPaymentForm(request.POST)
                if payment_form.is_valid():
                    try:
                        amount = Decimal(str(payment_form.cleaned_data['amount']))
                    except (InvalidOperation, KeyError):
                        messages.error(request, "Montant invalide.")
                        amount = None

                    if amount is not None and Decimal(str(event.price)) == amount:
                        # 🔹 Crée ou met à jour le Guest après paiement
                        guest, created = Guest.objects.update_or_create(
                            event_public=event,
                            email__iexact=user_email,
                            defaults={
                                'email': user_email,
                                'status': Guest.STATUS_ACCEPTED,
                                'payment_amount': amount,
                                'payment_status': 'paid',
                                'payment_transaction_id': f"PAY-{request.user.id}-{int(now_time.timestamp())}",
                                'payment_date': now_time
                            }
                        )

                        # 🔹 Crée ou met à jour le RSVP
                        rsvp, _ = RSVP.objects.update_or_create(
                            user=request.user,
                            event_public=event,
                            defaults={
                                'response': 'yes', 
                                'created_at': now_time
                            }
                        )

                        messages.success(request, "✅ Paiement effectué et participation enregistrée avec succès !")
                        return redirect('dashboard')  # Redirection vers le tableau de bord après création
                    else:
                        messages.error(request, f"Le montant doit être de {event.price:.2f} DT.")
            else:
                # Créer le formulaire avec la valeur initiale du prix
                payment_form = MockPaymentForm(initial={'amount': event.price})
    
    # Préparation du contexte initial
    context = {
        'event': event,
        'event_type': event_type,
        'now': now_time,
        'user_has_joined': user_has_joined,
        'display_price': display_price,
        'payment_form': payment_form,
        'has_paid': has_paid
    }

    # 🔹 Initialisation des variables pour la liste des participants
    guests = None
    participants = []
    participants_queryset = []
    total_rsvp = 0
    total_accepted = 0
    total_paid = 0
    user_participation = None
    
    # Initialiser UserModel pour la recherche des utilisateurs
    UserModel = get_user_model()

    # Récupération des participants pour les événements publics
    if event_type == 'public':
        # Récupérer tous les invités acceptés (pour les événements gratuits et payants)
        guests = Guest.objects.filter(
            event_public=event,
            status=Guest.STATUS_ACCEPTED
        ).select_related('event_public')
        
        # Debug: Afficher le nombre d'invités trouvés
        print(f"DEBUG - Nombre d'invités trouvés: {guests.count()}")
        for g in guests:
            print(f"  - {g.email}, Payé: {getattr(g, 'payment_status', 'N/A')}")
        
        # Pour les événements payants, ne montrer que ceux qui ont payé
        if event.is_paid and event.price is not None:
            guests = guests.filter(
                payment_status='paid',
                status=Guest.STATUS_ACCEPTED
            )
        
        # Récupérer les RSVP pour cet événement
        rsvps = RSVP.objects.filter(
            event_public=event,
            response='yes'
        ).select_related('user', 'user__userprofile')
        
        # Debug: Afficher le nombre de RSVP trouvés
        print(f"DEBUG - Nombre de RSVP trouvés: {rsvps.count()}")
        
        # Créer une liste unifiée des participants
        participants_list = []
        
        # Ajouter les invités
        for guest in guests:
            user_obj = UserModel.objects.filter(email__iexact=guest.email).first()
            participants_list.append({
                'guest': guest,
                'user': user_obj,
                'is_rsvp': False,
                'is_accepted': guest.status == Guest.STATUS_ACCEPTED,
                'is_paid': guest.payment_status == 'paid' if hasattr(guest, 'payment_status') else False
            })
            
            # Mettre à jour les totaux
            if guest.status == Guest.STATUS_ACCEPTED:
                total_accepted += 1
                if hasattr(guest, 'payment_status') and guest.payment_status == 'paid':
                    total_paid += 1
        
        # Ajouter les RSVP qui ne sont pas déjà dans la liste des invités
        for rsvp in rsvps:
            if not any(p['user'] == rsvp.user for p in participants_list):
                participants_list.append({
                    'guest': None,
                    'user': rsvp.user,
                    'is_rsvp': True,
                    'is_accepted': True,  # Un RSVP 'yes' est considéré comme accepté
                    'is_paid': False  # Les RSVP ne sont pas considérés comme payants
                })
                total_rsvp += 1
        
        # Mettre à jour le total RSVP (uniquement ceux qui n'ont pas d'entrée Guest)
        total_rsvp = len([p for p in participants_list if p['is_rsvp'] and not p['guest']])
        
        # Filtrer les participants si une recherche est effectuée
        search_query = request.GET.get('q', '').strip().lower()
        if search_query:
            participants_list = [
                p for p in participants_list 
                if (p['user'] and (search_query in p['user'].username.lower() or 
                                  search_query in p['user'].email.lower())) or
                   (p['guest'] and search_query in p['guest'].email.lower())
            ]
        
        # Pagination
        paginator = Paginator(participants_list, 10)  # 10 participants par page
        page = request.GET.get('page')
        
        try:
            participants = paginator.page(page)
        except PageNotAnInteger:
            participants = paginator.page(1)
        except EmptyPage:
            participants = paginator.page(paginator.num_pages)
            
        # Remove the duplicate pagination code below
        # The rest of the pagination logic is handled above
        
        # Vérifier la participation de l'utilisateur connecté
        if request.user.is_authenticated:
            user_participation = next(
                (p for p in participants_list if p['user'] == request.user),
                None
            )
            
            # Si l'utilisateur n'est pas dans la liste des participants mais a un RSVP
            if not user_participation:
                user_rsvp = next(
                    (p for p in participants_list if p['user'] == request.user and p['is_rsvp']),
                    None
                )
                if user_rsvp:
                    user_participation = user_rsvp

    # Afficher la liste des participants à tous les utilisateurs
        UserModel = get_user_model()

        # Recherche (filtre) des participants par nom ou email
        q = request.GET.get('q', '').strip()

        # Guests liés à l'événement
        if event_type == 'public':
            if event.is_paid and event.price is not None:
                # Pour les événements payants, on vérifie que le paiement a été effectué
                guests_qs = Guest.objects.filter(
                    event_public=event,
                    status=Guest.STATUS_ACCEPTED,
                    payment_status='paid'
                ).order_by('-created_at')
            else:
                # Pour les événements gratuits, on vérifie seulement le statut
                guests_qs = Guest.objects.filter(
                    event_public=event,
                    status=Guest.STATUS_ACCEPTED
                ).order_by('-created_at')
                
            # Ajouter les RSVPs pour les événements publics
            rsvps_qs = RSVP.objects.filter(
                event_public=event,
                response='yes'
            ).select_related('user').order_by('-created_at')
            
            # Si l'utilisateur n'est pas l'organisateur, ne montrer que les participants acceptés
            if request.user != event.owner:
                guests_qs = guests_qs.filter(status=Guest.STATUS_ACCEPTED)
                
        else:
            # Pour les événements privés, on vérifie seulement le statut
            guests_qs = Guest.objects.filter(
                event_private=event,
                status=Guest.STATUS_ACCEPTED
            ).order_by('-created_at')
            
            # Pour les événements privés, on ne montre que les invités acceptés
            if request.user != event.owner:
                guests_qs = guests_qs.filter(status=Guest.STATUS_ACCEPTED)
                
            rsvps_qs = RSVP.objects.none()  # Pas de RSVP pour les événements privés
        # Filtrer par recherche si nécessaire
        if q:
            guests_qs = guests_qs.filter(Q(email__icontains=q))
            if 'rsvps_qs' in locals():
                rsvps_qs = rsvps_qs.filter(
                    Q(user__username__icontains=q) | 
                    Q(user__email__icontains=q) |
                    Q(user__first_name__icontains=q) |
                    Q(user__last_name__icontains=q)
                )

        # Pour événements publics, récupérer aussi les RSVPs (utilisateurs ayant répondu 'yes')
        rsvp_users = []
        if event_type == 'public':
            if 'rsvps_qs' not in locals():
                rsvps_qs = RSVP.objects.filter(
                    event_public=event, 
                    response='yes'
                ).select_related('user')
                
            rsvp_users = [r.user for r in rsvps_qs]
            total_rsvp = rsvps_qs.count()

        # Totaux par Guest — filtrer selon le type d'événement pour éviter les erreurs de type
        if event_type == 'public':
            total_accepted = Guest.objects.filter(event_public=event, status=Guest.STATUS_ACCEPTED).count()
            total_paid = Guest.objects.filter(event_public=event, payment_status='paid').count()
        else:
            total_accepted = Guest.objects.filter(event_private=event, status=Guest.STATUS_ACCEPTED).count()
            # Les événements privés n'ont pas de paiement via Guest.event_public
            total_paid = 0

        seen_emails = set()

        # Ajouter les Guests
        for g in guests_qs:
            linked_user = UserModel.objects.filter(email__iexact=g.email).first()
            participants_queryset.append({
                'guest': g,
                'user': linked_user,
                'is_rsvp': linked_user in rsvp_users if linked_user else False,
                'is_paid': (g.payment_status == 'paid'),
                'is_accepted': (g.status == Guest.STATUS_ACCEPTED),
            })
            if g.email:
                seen_emails.add(g.email.lower())

        # Ajouter les RSVPs qui n'ont pas de Guest correspondant
        if event_type == 'public':
            for user in rsvp_users:
                if user.email and user.email.lower() in seen_emails:
                    continue
                # user a RSVP mais pas de guest
                participants_queryset.append({
                    'guest': None,
                    'user': user,
                    'is_rsvp': True,
                    'is_paid': False,
                    'is_accepted': False,
                })

        # Pagination is already handled above
        # Remove duplicate pagination code


    # Debug: Afficher le nombre de participants dans la console serveur
    print(f"DEBUG - Nombre de participants: {len(participants) if participants else 0}")
    print(f"DEBUG - participants est de type: {type(participants)}")
    
    return render(request, 'events/event_detail.html', {
        'event': event,
        'payment_form': payment_form,
        'participants': participants,
        'participants_page': participants if isinstance(participants, object) else None,
        'now': now_time,
        'event_type': event_type,
        'user_has_joined': user_has_joined,
        'display_price': display_price,
        'total_rsvp': total_rsvp,
        'total_accepted': total_accepted,
        'total_paid': total_paid,
        'user_participation': user_participation if 'user_participation' in locals() else None,
    })



@login_required
def join_event(request, event_id):
    event = get_object_or_404(PrivateEvent, id=event_id)
    guest, _ = Guest.objects.get_or_create(event_private=event, email=request.user.email)
    guest.status = Guest.STATUS_ACCEPTED
    guest.save()
    messages.success(request, f"🎉 Vous avez rejoint l'événement '{event.title}' !")
    return redirect('event_detail', event_type='public', event_id=event.id)


def register_user_to_public_event(user, event, *, paid=False, amount=None, transaction_id=None):
    """
    Inscrit proprement un utilisateur à un événement public
    (gratuit ou payant)
    """
    email = user.email.strip().lower()
    now = timezone.now()

    # 🔹 Guest
    guest, created = Guest.objects.get_or_create(
        event_public=event,
        email__iexact=email,
        defaults={
            'email': email,
            'status': Guest.STATUS_ACCEPTED,
        }
    )

    guest.status = Guest.STATUS_ACCEPTED

    if paid:
        guest.payment_status = 'paid'
        guest.payment_amount = Decimal(str(amount)) if amount else None
        guest.payment_transaction_id = transaction_id
        guest.payment_date = now

    guest.save()

    # 🔹 RSVP
    rsvp, _ = RSVP.objects.get_or_create(
        user=user,
        event_public=event,
        defaults={'response': 'yes', 'created_at': now}
    )
    rsvp.response = 'yes'
    rsvp.save()

    return guest


@login_required
def join_public_event(request, event_id):
    event = get_object_or_404(PublicEvent, id=event_id)
    
    if localtime(event.date) < localtime(now()):
        messages.error(request, "⏰ L'événement est déjà passé.")
        return redirect('event_detail', event_type='public', event_id=event.id)

    if event.is_paid and event.price and event.price > 0:
        messages.info(request, "Cet événement est payant. Veuillez procéder au paiement.")
        return redirect('event_payment', event_id=event.id)

    # Pour les événements gratuits
    register_user_to_public_event(
        user=request.user,
        event=event,
        paid=False
    )

    messages.success(request, f"🎉 Vous participez à l'événement '{event.title}' !")
    return redirect('event_detail', event_type='public', event_id=event.id)
    return redirect('event_payment', event_id=event.id)


# ================================
# Payments
# ================================

@login_required
def payment_view(request, event_id):
    event = get_object_or_404(PublicEvent, id=event_id)
    # Utiliser MockPaymentForm pour valider les données avant de marquer payé
    if request.method == 'POST':
        form = MockPaymentForm(request.POST)
        if form.is_valid():
            try:
                amount = Decimal(str(form.cleaned_data['amount']))
            except (InvalidOperation, KeyError):
                messages.error(request, "Montant invalide.")
                return render(request, 'events/payment.html', {'event': event, 'form': form})

            if event.price is not None and Decimal(str(event.price)) == amount:
                guest, created = Guest.objects.get_or_create(
                    event_public=event,
                    email=request.user.email,
                    defaults={
                        'status': Guest.STATUS_ACCEPTED,
                        'payment_amount': amount,
                        'payment_status': 'paid',
                        'payment_transaction_id': f"MOCK-{request.user.id}-{int(timezone.now().timestamp())}",
                        'payment_date': timezone.now()
                    }
                )
                if not created:
                    guest.status = Guest.STATUS_ACCEPTED
                    guest.payment_amount = amount
                    guest.payment_status = 'paid'
                    guest.payment_transaction_id = f"MOCK-{request.user.id}-{int(timezone.now().timestamp())}"
                    guest.payment_date = timezone.now()
                    guest.save()

                # Créer ou mettre à jour le RSVP
                rsvp, r_created = RSVP.objects.get_or_create(
                    user=request.user,
                    event_public=event,
                    defaults={'response': 'yes', 'created_at': timezone.now()}
                )
                if not r_created:
                    rsvp.response = 'yes'
                    rsvp.save()

                messages.success(request, "💳 Paiement effectué avec succès ! Vous êtes maintenant participant de cet événement.")
                return redirect('dashboard')  # Redirection vers le tableau de bord après création
            else:
                messages.error(request, f"Le montant doit être de {event.price:.2f} €.")
        else:
            messages.error(request, "Veuillez corriger les erreurs du formulaire de paiement.")
        return render(request, 'events/payment.html', {'event': event, 'form': form})

    # GET → afficher le formulaire
    form = MockPaymentForm(initial={'amount': event.price})
    return render(request, 'events/payment.html', {'event': event, 'form': form})


@login_required
def payment_success(request, event_id):
    event = get_object_or_404(PublicEvent, id=event_id)
    return render(request, 'events/payment_success.html', {'event': event})

# ================================
# Payments
# ================================

from decimal import Decimal, InvalidOperation
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import PublicEvent, Guest, RSVP
from .forms import MockPaymentForm

from decimal import Decimal, InvalidOperation
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import PublicEvent, Guest, RSVP
from .forms import MockPaymentForm

from decimal import Decimal, InvalidOperation
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import PublicEvent, Guest, RSVP
from .forms import MockPaymentForm

@login_required
def event_payment(request, event_id):
    event = get_object_or_404(PublicEvent, id=event_id)
    
    if not event.is_paid or event.price is None or event.price <= 0:
        messages.error(request, "Cet événement ne nécessite pas de paiement.")
        return redirect('event_detail', event_type='public', event_id=event_id)
    
    # Vérifie si l'utilisateur a déjà payé (avec correspondance insensible à la casse)
    if Guest.objects.filter(
        event_public=event,
        email__iexact=request.user.email,
        payment_status='paid'
    ).exists():
        messages.info(request, "Vous êtes déjà inscrit à cet événement.")
        return redirect('event_detail', event_type='public', event_id=event.id)
    
    if request.method == 'POST':
        form = MockPaymentForm(request.POST)
        if form.is_valid():
            try:
                amount = Decimal(str(form.cleaned_data['amount']))
            except (InvalidOperation, KeyError):
                messages.error(request, "Montant invalide.")
                return render(request, 'events/event_payment.html', {'event': event, 'form': form, 'display_price': f"{event.price:.2f}"})
            
            if amount != Decimal(str(event.price)):
                messages.error(request, f"Le montant doit être de {event.price:.2f} €.")
            else:
                # Utilisation de la fonction centrale pour enregistrer l'utilisateur
                register_user_to_public_event(
                    user=request.user,
                    event=event,
                    paid=True,
                    amount=amount,
                    transaction_id=f"MOCK-{request.user.id}-{int(timezone.now().timestamp())}"
                )
                
                messages.success(request, "💳 Paiement effectué avec succès ! Vous êtes maintenant participant de cet événement.")
                return redirect('dashboard')  # Redirection vers le tableau de bord après création
        else:
            messages.error(request, "Veuillez corriger les erreurs du formulaire.")
    else:
        form = MockPaymentForm(initial={'amount': event.price})
    
    return render(request, 'events/event_payment.html', {
        'event': event,
        'form': form,
        'display_price': f"{event.price:.2f}"
    })


@login_required
def edit_public_event(request, event_id):
    event = get_object_or_404(PublicEvent, id=event_id, owner=request.user)

    if request.method == "POST":
        form = PublicEventForm(request.POST, request.FILES, instance=event)

        if form.is_valid():
            # Use the form to apply cleaned values (is_paid boolean, price, etc.)
            updated_event = form.save(commit=False)
            updated_event.save()
            messages.success(request, "✅ Événement public mis à jour !")
            return redirect("dashboard")

        else:
            messages.error(request, "❌ Veuillez corriger les erreurs.")

    else:
        # Valeurs initiales cohérentes
        initial_data = {
            "is_paid": "paid" if event.is_paid else "free",
            "price": event.price if event.is_paid else "",
            "max_participants": event.max_participants,
        }

        form = PublicEventForm(instance=event, initial=initial_data)

    return render(
        request,
        "events/edit_public_event.html",
        {"form": form, "event": event},
    )

@login_required
def edit_private_event(request, event_id):
    """
    Vue pour modifier un événement privé existant.
    Seul le propriétaire de l'événement peut le modifier.
    """
    event = get_object_or_404(PrivateEvent, id=event_id)
    
    # Vérifier que l'utilisateur est bien le propriétaire de l'événement
    if request.user != event.owner:
        messages.error(request, "Vous n'êtes pas autorisé à modifier cet événement.")
        return redirect('event_detail', event_type='public', event_id=event.id)
    
    if request.method == 'POST':
        form = PrivateEventForm(request.POST, request.FILES, instance=event)
        
        if form.is_valid():
            event = form.save(commit=False)
            
            # Gestion des invités
            guests_emails = form.cleaned_data.get('guests_emails', '')
            if guests_emails is not None:  # Vérifier que le champ n'est pas None
                # Supprimer les invités existants pour cet événement
                Guest.objects.filter(event_private=event).delete()
                
                # Ajouter les nouveaux invités
                for email in [e.strip() for e in guests_emails.split(',') if e.strip()]:
                    Guest.objects.create(
                        event_private=event,
                        email=email,
                        status=Guest.STATUS_PENDING
                    )
            
            event.save()
            messages.success(request, "L'événement privé a été mis à jour avec succès !")
            return redirect('dashboard')  # Redirection vers le tableau de bord après création
    else:
        # Pré-remplir les emails des invités existants
        initial = {
            'guests_emails': ', '.join([guest.email for guest in event.guests.all()])
        }
        form = PrivateEventForm(instance=event, initial=initial)
    
    return render(request, 'events/edit_private_event.html', {
        'form': form,
        'event': event
    })


@login_required
def delete_confirm(request, event_id):
    """
    Vue pour confirmer la suppression d'un événement.
    """
    # Vérifier si c'est un événement public
    try:
        event = get_object_or_404(PublicEvent, id=event_id, owner=request.user)
        event_type = 'public'
    except PublicEvent.DoesNotExist:
        # Si ce n'est pas un événement public, vérifier si c'est un événement privé
        try:
            event = get_object_or_404(PrivateEvent, id=event_id, owner=request.user)
            event_type = 'private'
        except PrivateEvent.DoesNotExist:
            messages.error(request, "Événement introuvable ou vous n'êtes pas autorisé à le supprimer.")
            return redirect('dashboard')  # Redirection vers le tableau de bord après création

    if request.method == 'POST':
        # Supprimer l'événement
        event.delete()
        messages.success(request, "L'événement a été supprimé avec succès !")
        return redirect('event_detail', event_type='public', event_id=event.id)

    # Afficher la page de confirmation
    return render(request, 'events/delete_confirm.html', {
        'event': event,
        'event_type': event_type
    })


def rsvp(request, token):
    """
    Vue pour gérer les réponses aux invitations (Accepté/Refusé)
    via un lien unique ou QR code envoyé par email.
    """
    try:
        # Trouver l'invité avec le token fourni
        guest = get_object_or_404(Guest, token=token)
        
        # Récupérer l'événement associé (privé ou public)
        event = guest.event_private if hasattr(guest, 'event_private') else guest.event_public
        is_private = hasattr(guest, 'event_private')
        
        if event is None:
            messages.error(request, "Événement introuvable.")
            return redirect('home')
            
        # Vérifier si l'invitation est toujours valide
        if guest.status != 'pending':
            messages.info(
                request, 
                f"Vous avez déjà répondu à cette invitation : {guest.get_status_display()}"
            )
            return redirect('dashboard')  # Redirection vers le tableau de bord après création
        
        # Vérifier si l'événement est déjà passé
        if event.date < timezone.now():
            messages.warning(request, "Cet événement est déjà terminé.")
            return redirect('home')
        
        # Traitement de la réponse
        if request.method == 'POST':
            response = request.POST.get('response')
            
            if response in ['accepted', 'declined']:
                # Mettre à jour le statut de l'invité
                guest.status = response
                guest.response_date = timezone.now()
                guest.save()
                
                # Mettre à jour ou créer le RSVP pour les événements privés et publics
                if request.user.is_authenticated:
                    if is_private:
                        RSVP.objects.update_or_create(
                            user=request.user,
                            event_private=event,
                            defaults={'response': 'yes' if response == 'accepted' else 'no'}
                        )
                    else:
                        RSVP.objects.update_or_create(
                            user=request.user,
                            event_public=event,
                            defaults={'response': 'yes' if response == 'accepted' else 'no'}
                        )
                
                # Envoyer un email de confirmation
                try:
                    from .utils.email_utils import send_rsvp_confirmation
                    send_rsvp_confirmation(guest, event, response)
                except Exception as e:
                    logger.error(f"Erreur lors de l'envoi de la confirmation RSVP: {str(e)}")
                
                messages.success(
                    request, 
                    f"Votre réponse a été enregistrée : {guest.get_status_display()}"
                )
                
                # Rediriger vers le tableau de bord
                return redirect('dashboard')  # Redirection vers le tableau de bord après création
            else:
                messages.error(request, "Réponse invalide.")
        
        # Afficher le formulaire de réponse
        context = {
            'guest': guest,
            'event': event,
            'token': token,
            'now': timezone.now(),
            'is_organizer': request.user == event.owner if hasattr(event, 'owner') else False
        }
        return render(request, 'events/rsvp.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans la vue RSVP: {str(e)}", exc_info=True)
        messages.error(
            request, 
            "Une erreur est survenue lors du traitement de votre réponse. "
            "Veuillez réessayer ou contacter l'organisateur de l'événement."
        )
        return redirect('home')


def rsvp_confirm(request, token):
    """
    Vue pour confirmer la réponse à une invitation.
    Cette vue est appelée après que l'utilisateur a répondu au formulaire RSVP.
    """
    try:
        # Trouver l'invité avec le token fourni
        guest = Guest.objects.get(rsvp_token=token)
        
        # Récupérer l'événement associé
        event = guest.event_private if hasattr(guest, 'event_private') else guest.event_public
        
        # Si l'utilisateur n'est pas connecté, le rediriger vers la page de connexion
        if not request.user.is_authenticated:
            messages.info(request, "Veuillez vous connecter pour confirmer votre présence.")
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        
        # Vérifier si l'utilisateur a déjà répondu
        if guest.status != Guest.STATUS_PENDING:
            messages.info(request, f"Vous avez déjà répondu à cette invitation : {guest.get_status_display()}")
            return redirect('dashboard')  # Redirection vers le tableau de bord après création
        
        # Traiter la confirmation
        if request.method == 'POST':
            response = request.POST.get('response')
            
            if response in ['accept', 'decline']:
                # Mettre à jour le statut de l'invité
                guest.status = Guest.STATUS_ACCEPTED if response == 'accept' else Guest.STATUS_DECLINED
                guest.rsvp_token_used = True
                guest.response_date = timezone.now()
                guest.save()
                
                # Si l'utilisateur est connecté, créer un RSVP pour les événements publics
                if hasattr(guest, 'event_public'):
                    RSVP.objects.update_or_create(
                        user=request.user,
                        event_public=guest.event_public,
                        defaults={'response': 'yes' if response == 'accept' else 'no'}
                    )
                
                messages.success(
                    request, 
                    f"Votre réponse a été enregistrée : {guest.get_status_display()}"
                )
                return redirect('dashboard')  # Redirection vers le tableau de bord après création
        
        # Afficher la page de confirmation
        return render(request, 'events/rsvp_confirm.html', {
            'guest': guest,
            'event': event,
            'token': token
        })
        
    except Guest.DoesNotExist:
        messages.error(request, "Lien de confirmation invalide ou expiré.")
        return redirect('event_detail', event_type='public', event_id=event.id)


@login_required
def profile(request):
    """
    Vue pour afficher le profil de l'utilisateur.
    """
    # Récupérer le profil de l'utilisateur ou le créer s'il n'existe pas
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Récupérer les événements créés par l'utilisateur
    created_events = {
        'public_events': PublicEvent.objects.filter(owner=request.user).order_by('-created_at'),
        'private_events': PrivateEvent.objects.filter(owner=request.user).order_by('-created_at')
    }
    
    # Récupérer les événements auxquels l'utilisateur participe
    participating_events = {
        'public_rsvps': RSVP.objects.filter(user=request.user, response='yes').select_related('event_public'),
        'private_invites': Guest.objects.filter(
            email=request.user.email, 
            status=Guest.STATUS_ACCEPTED
        ).select_related('event_private')
    }
    
    context = {
        'profile': profile,
        'organized_events': list(created_events['public_events']) + list(created_events['private_events']),
        'invited_events': list(participating_events['public_rsvps']) + list(participating_events['private_invites']),
    }
    
    return render(request, 'events/profile.html', context)


def user_profile(request, user_id):
    """
    Vue publique pour afficher le profil d'un utilisateur par son ID.
    Visible à tous, mais certaines informations restent privées.
    """
    UserModel = get_user_model()
    try:
        profile_user = UserModel.objects.get(id=user_id)
    except UserModel.DoesNotExist:
        raise Http404("Utilisateur introuvable")

    profile, _ = UserProfile.objects.get_or_create(user=profile_user)

    # Récupérer les événements publics organisés par cet utilisateur
    organized_events = PublicEvent.objects.filter(owner=profile_user).order_by('-created_at')

    context = {
        'profile_user': profile_user,
        'profile': profile,
        'organized_events': organized_events,
        'is_owner': request.user.is_authenticated and request.user.id == profile_user.id,
    }

    return render(request, 'events/user_profile.html', context)


@login_required
def edit_profile(request):
    """
    Vue pour modifier le profil de l'utilisateur.
    """
    # Récupérer le profil de l'utilisateur ou le créer s'il n'existe pas
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Mise à jour des informations de l'utilisateur
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(
            request.POST, 
            request.FILES, 
            instance=profile
        )
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès !')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    
    return render(request, 'events/edit_profile.html', context)


def statistiques(request):
    """
    Vue pour afficher les statistiques du site
    """
    # Statistiques de base
    total_utilisateurs = User.objects.count()
    total_evenements = PublicEvent.objects.count() + PrivateEvent.objects.count()
    
    # Calculer le nombre total de participations
    total_participations = RSVP.objects.filter(response='yes').count() + \
                          Guest.objects.filter(status='accepted').count()
    
    # Événements à venir (dans les 30 prochains jours) — inclure publics et privés
    date_limite = timezone.now() + timedelta(days=30)

    upcoming_public = PublicEvent.objects.filter(date__gte=timezone.now(), date__lte=date_limite).order_by('date')
    upcoming_private = PrivateEvent.objects.filter(date__gte=timezone.now(), date__lte=date_limite).order_by('date')

    # Fonction utilitaire pour calculer le nombre de participants réel d'un événement
    def count_participants_for_event(ev):
        # Pour les événements publics : compter les RSVPs 'yes' + guests acceptés/paid
        if isinstance(ev, PublicEvent):
            rsvp_count = RSVP.objects.filter(event_public=ev, response='yes').count()
            guest_count = Guest.objects.filter(event_public=ev, status=Guest.STATUS_ACCEPTED).count()
            paid_count = Guest.objects.filter(event_public=ev, payment_status='paid').count()
            # Éviter le double comptage : guests payés sont généralement marked accepted too,
            # mais on prend le max entre (rsvp_count + guest_count) et paid_count pour être conservateur
            total = rsvp_count + guest_count
            # Si paid_count est greater than guest_count, prefer paid_count (covers paid but not accepted)
            if paid_count > guest_count:
                total = rsvp_count + paid_count
            return total
        else:
            # Pour événements privés : compter les guests acceptés
            return Guest.objects.filter(event_private=ev, status=Guest.STATUS_ACCEPTED).count()

    # Construire une liste d'objets simples pour le template avec participants_count et max_participants
    def make_event_summary(ev):
        return {
            'instance': ev,
            'title': getattr(ev, 'title', ''),
            'date': getattr(ev, 'date', None),
            'participants_count': count_participants_for_event(ev),
            'max_participants': getattr(ev, 'max_participants', None),
        }

    upcoming = [make_event_summary(e) for e in list(upcoming_public) + list(upcoming_private)]
    upcoming.sort(key=lambda x: x['date'] or timezone.now())
    evenements_a_venir = upcoming[:5]

    # Top événements : combiner publics et privés et trier par participants_count
    all_public = list(PublicEvent.objects.all())
    all_private = list(PrivateEvent.objects.all())
    all_events = all_public + all_private
    top_list = [make_event_summary(e) for e in all_events]
    top_list.sort(key=lambda x: x['participants_count'], reverse=True)
    top_evenements = top_list[:5]
    
    # Préparation des données pour le graphique d'évolution mensuelle
    from django.db.models.functions import TruncMonth
    
    # Événements par mois
    evenements_par_mois = {}
    mois = []
    
    # Récupérer les 12 derniers mois
    for i in range(11, -1, -1):
        date = timezone.now() - timedelta(days=30*i)
        mois_str = date.strftime('%Y-%m')
        mois_nom = date.strftime('%b %Y')
        mois.append(mois_nom)
        evenements_par_mois[mois_str] = 0
    
    # Compter les événements par mois (publics + privés)
    for event in list(PublicEvent.objects.all()) + list(PrivateEvent.objects.all()):
        try:
            mois_str = event.date.strftime('%Y-%m')
        except Exception:
            continue
        if mois_str in evenements_par_mois:
            evenements_par_mois[mois_str] += 1
    
    # Préparer les données pour le graphique
    donnees_graphique = [evenements_par_mois[m] for m in sorted(evenements_par_mois.keys())]
    
    context = {
        'total_utilisateurs': total_utilisateurs,
        'total_evenements': total_evenements,
        'total_participations': total_participations,
        'evenements_a_venir': evenements_a_venir,
        'top_evenements': top_evenements,
        'mois': json.dumps(mois),
        'evenements_par_mois': json.dumps(donnees_graphique),
    }
    
    return render(request, 'events/statistiques.html', context)
