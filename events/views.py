from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from .models import Event, Guest
import qrcode
from io import BytesIO
import base64

# Tableau de bord des événements
@login_required
def dashboard(request):
    events = Event.objects.filter(owner=request.user)
    event_data = []

    for event in events:
        guests = Guest.objects.filter(event=event)
        accepted = guests.filter(status='Accepted').count()
        declined = guests.filter(status='Declined').count()
        pending = guests.filter(status='Pending').count()

        # Génération du QR code pour l'événement
        qr = qrcode.QRCode(version=1, box_size=5, border=4)
        url = request.build_absolute_uri(f'/rsvp/{event.id}/')
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()

        event_data.append({
            'event': event,
            'guests': guests,
            'accepted': accepted,
            'declined': declined,
            'pending': pending,
            'qr_code': img_str,
        })

    return render(request, 'events/dashboard.html', {'event_data': event_data})


# Ajouter un événement
@login_required
def add_event(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        date = request.POST.get('date')
        location = request.POST.get('location')
        guests_emails = request.POST.get('guests_emails')

        event = Event.objects.create(
            owner=request.user,
            title=title,
            description=description,
            date=date,
            location=location,
            guests_emails=guests_emails
        )

        # Créer les invités
        for email in guests_emails.split(','):
            Guest.objects.create(event=event, email=email.strip())

        # Envoyer un e-mail à chaque invité
        for email in guests_emails.split(','):
            guest_email = email.strip()
            rsvp_link = f"http://127.0.0.1:8000/rsvp/{event.id}/{guest_email}"
            send_mail(
                subject=f"Invitation à {title}",
                message=(
                    f"Vous êtes invité à l'événement '{title}' le {date} à {location}.\n\n"
                    f"➡️ Confirmez votre présence ici : {rsvp_link}"
                ),
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[guest_email],
                fail_silently=False,
            )

        messages.success(request, "L'événement et les invitations ont été envoyés avec succès 🎉")
        return redirect('dashboard')

    return render(request, 'events/add_event.html')


# Inscription utilisateur
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'events/register.html', {'form': form})


# Gestion des réponses RSVP
def rsvp(request, event_id, guest_email):
    event = get_object_or_404(Event, id=event_id)
    guest_obj, created = Guest.objects.get_or_create(event=event, email=guest_email)

    if request.method == 'POST':
        choice = request.POST.get('choice')  # 'Accepted' ou 'Declined'
        if choice in ['Accepted', 'Declined']:
            guest_obj.status = choice
            guest_obj.save()

            message = (
                "Merci d’avoir confirmé votre présence 🎉"
                if choice == "Accepted"
                else "Votre refus a bien été enregistré 😢"
            )

            return render(request, 'events/rsvp_confirm.html', {
                'event': event,
                'guest_email': guest_email,
                'message': message,
            })

    return render(request, 'events/rsvp.html', {
        'event': event,
        'guest_email': guest_email,
        'guest': guest_obj
    })
