import json
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

from .models import TwoFactorAuth, TwoFactorCode
from .forms import TwoFactorVerificationForm, Toggle2FAForm

def two_factor_verify(request):
    """
    Affiche le formulaire de vérification 2FA avec gestion améliorée des erreurs
    """
    print("=== DEBUG: Début de two_factor_verify ===")
    
    # Vérifier si l'utilisateur a une session 2FA en attente
    pending_user_id = request.session.get('pending_2fa_user_id')
    user = None
    
    # Récupérer l'utilisateur
    if pending_user_id:
        User = get_user_model()
        try:
            user = User.objects.get(id=pending_user_id)
            two_fa, created = TwoFactorAuth.objects.get_or_create(user=user)
            print(f"DEBUG: Utilisateur trouvé: {user.username}, 2FA activée: {two_fa.is_enabled}")
            
            # Si la 2FA n'est pas activée, connecter l'utilisateur directement
            if not two_fa.is_enabled:
                if hasattr(user, 'backend'):
                    login(request, user)
                if 'pending_2fa_user_id' in request.session:
                    del request.session['pending_2fa_user_id']
                return redirect('dashboard')
                
        except (User.DoesNotExist, KeyError) as e:
            print(f"DEBUG: Erreur utilisateur: {str(e)}")
            if 'pending_2fa_user_id' in request.session:
                del request.session['pending_2fa_user_id']
            return redirect('login')
    elif request.user.is_authenticated:
        # Si l'utilisateur est déjà authentifié mais n'a pas de session 2FA en attente
        user = request.user
        two_fa, created = TwoFactorAuth.objects.get_or_create(user=user)
        print(f"DEBUG: Utilisateur déjà authentifié: {user.username}")
        
        # Si la 2FA n'est pas activée, rediriger vers le tableau de bord
        if not two_fa.is_enabled:
            return redirect('dashboard')
    else:
        # Si aucun utilisateur n'est authentifié et aucune session 2FA en attente
        print("DEBUG: Aucun utilisateur trouvé, redirection vers login")
        return redirect('login')
    
    # Si l'utilisateur a une session 2FA valide, rediriger
    if request.session.get('2fa_verified', False):
        next_url = request.session.get('next', 'dashboard')
        if 'next' in request.session:
            del request.session['next']
        if 'pending_2fa_user_id' in request.session:
            del request.session['pending_2fa_user_id']
        return redirect(next_url)
    
    # Gestion de la soumission du formulaire
    if request.method == 'POST':
        print("DEBUG: Requête POST reçue")
        form = TwoFactorVerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            print(f"DEBUG: Code reçu: {code}")
            
            # Vérifier le code
            try:
                two_fa = TwoFactorAuth.objects.get(user=user)
                if two_fa.verify_code(code):
                    print("DEBUG: Code valide")
                    # Marquer la session comme vérifiée
                    request.session['2fa_verified'] = True
                    request.session['2fa_verified_at'] = timezone.now().isoformat()
                    
                    # Connecter l'utilisateur s'il n'est pas déjà connecté
                    if not request.user.is_authenticated:
                        user.backend = 'django.contrib.auth.backends.ModelBackend'
                        login(request, user)
                    
                    if 'pending_2fa_user_id' in request.session:
                        del request.session['pending_2fa_user_id']
                    
                    # Rediriger vers l'URL demandée ou le tableau de bord
                    next_url = request.session.get('next', 'dashboard')
                    if 'next' in request.session:
                        del request.session['next']
                    
                    messages.success(request, 'Connexion réussie avec authentification à deux facteurs.')
                    return redirect(next_url)
                else:
                    print("DEBUG: Code invalide")
                    messages.error(request, 'Code de vérification invalide ou expiré.')
            except TwoFactorAuth.DoesNotExist:
                print("DEBUG: Erreur - TwoFactorAuth n'existe pas")
                messages.error(request, "Une erreur s'est produite. Veuillez réessayer.")
    else:
        form = TwoFactorVerificationForm()
    
    # Envoyer un nouveau code si nécessaire
    code_sent = False
    try:
        two_fa = TwoFactorAuth.objects.get(user=user)
        print(f"DEBUG: Envoi du code à {user.email}")
        code_sent = two_fa.send_verification_email(request)
        print(f"DEBUG: Code envoyé: {code_sent}")
    except Exception as e:
        print(f"DEBUG: Erreur lors de l'envoi du code: {str(e)}")
    
    return render(request, 'registration/two_factor_verify.html', {
        'form': form,
        'email': user.email,
        'code_sent': code_sent
    })

@login_required
def toggle_two_factor(request):
    """
    Active ou désactive l'authentification à deux facteurs
    """
    try:
        two_fa = request.user.two_factor_auth
    except TwoFactorAuth.DoesNotExist:
        two_fa = TwoFactorAuth.objects.create(user=request.user, is_enabled=False)
    
    if request.method == 'POST':
        form = Toggle2FAForm(request.POST)
        if form.is_valid():
            enable_2fa = form.cleaned_data['enable_2fa']
            
            if enable_2fa and not two_fa.is_enabled:
                # Activer la 2FA et envoyer un code de vérification
                two_fa.is_enabled = True
                two_fa.save()
                two_fa.send_verification_email(request)
                messages.success(request, 'Authentification à deux facteurs activée. Un code de vérification a été envoyé à votre adresse email.')
                return redirect('two_factor_verify')
            elif not enable_2fa and two_fa.is_enabled:
                # Désactiver la 2FA
                two_fa.is_enabled = False
                two_fa.save()
                messages.success(request, 'Authentification à deux facteurs désactivée avec succès.')
                return redirect('profile')
    else:
        form = Toggle2FAForm(initial={'enable_2fa': two_fa.is_enabled})
    
    return render(request, 'registration/toggle_two_factor.html', {
        'form': form,
        'two_fa_enabled': two_fa.is_enabled
    })

# Middleware pour vérifier la 2FA
class TwoFactorMiddleware:
    """
    Middleware pour gérer l'authentification à deux facteurs
    La 2FA est obligatoire pour tous les utilisateurs
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Liste des URLs qui ne nécessitent pas de 2FA
        exempt_urls = [
            '/accounts/login/',
            '/accounts/logout/',
            '/accounts/password_reset/',
            '/accounts/reset/',
            '/admin/',
            '/static/',
            '/media/',
            '/two-factor/verify/',
            '/two-factor/resend-code/',
        ]

        # Si l'URL est dans la liste des URLs exemptées, on ne fait rien
        if any(request.path.startswith(url) for url in exempt_urls):
            return self.get_response(request)

        # Si l'utilisateur n'est pas authentifié, on ne fait rien
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Vérifier si l'utilisateur a une configuration 2FA
        try:
            two_fa = request.user.two_factor_auth
        except TwoFactorAuth.DoesNotExist:
            # Si l'utilisateur n'a pas de configuration 2FA, on en crée une activée
            two_fa = TwoFactorAuth.objects.create(user=request.user, is_enabled=True)
            # On redirige vers la page de vérification 2FA
            request.session['pending_2fa_user_id'] = request.user.id
            return redirect('two_factor_verify')

        # Vérifier si la session 2FA est valide (moins de 24h)
        two_fa_verified = request.session.get('2fa_verified', False)
        two_fa_verified_at = request.session.get('2fa_verified_at')
        
        if two_fa_verified and two_fa_verified_at:
            from datetime import datetime, timedelta
            from django.utils.timezone import make_aware
            
            try:
                verified_at = datetime.fromisoformat(two_fa_verified_at)
                if not verified_at.tzinfo:
                    verified_at = make_aware(verified_at)
                    
                if datetime.now(verified_at.tzinfo) - verified_at < timedelta(hours=24):
                    return self.get_response(request)
            except (ValueError, TypeError) as e:
                # En cas d'erreur de format de date, on force une nouvelle vérification
                pass

        # Si on arrive ici, la 2FA est requise
        if 'pending_2fa_user_id' not in request.session:
            request.session['pending_2fa_user_id'] = request.user.id
        return redirect('two_factor_verify')


@csrf_exempt
def resend_verification_code(request):
    """
    Vue pour renvoyer un nouveau code de vérification 2FA
    """
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            two_fa = request.user.two_factor_auth
            if two_fa.is_enabled:
                code_sent = two_fa.send_verification_email(request)
                if code_sent:
                    return JsonResponse({'success': True, 'message': 'Un nouveau code a été envoyé à votre adresse email.'})
                else:
                    return JsonResponse({'success': False, 'message': 'Impossible d\'envoyer le code. Veuillez réessayer plus tard.'}, status=400)
            else:
                return JsonResponse({'success': False, 'message': 'L\'authentification à deux facteurs n\'est pas activée pour votre compte.'}, status=400)
        except TwoFactorAuth.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Configuration 2FA introuvable.'}, status=400)
    
    return JsonResponse({'success': False, 'message': 'Requête invalide.'}, status=400)
