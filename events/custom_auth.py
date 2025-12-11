from django.contrib.auth import login as auth_login, authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render
from django.contrib import messages
from django.conf import settings
from django.db import transaction
from .models import TwoFactorAuth, TwoFactorCode
import logging

logger = logging.getLogger(__name__)

@transaction.atomic
def login_with_2fa(request):
    """
    Vue personnalisée pour gérer la connexion avec 2FA
    La 2FA est activée par défaut pour tous les utilisateurs
    """
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                # Créer ou récupérer la configuration 2FA
                two_fa, created = TwoFactorAuth.objects.get_or_create(
                    user=user,
                    defaults={'is_enabled': True}  # 2FA activée par défaut
                )
                
                # Si la 2FA est activée pour cet utilisateur
                if two_fa.is_enabled:
                    try:
                        # Connecter l'utilisateur sans créer de session complète
                        user.backend = 'django.contrib.auth.backends.ModelBackend'
                        auth_login(request, user)
                        
                        # Stocker l'info que l'utilisateur doit valider la 2FA
                        request.session['pending_2fa_user_id'] = user.id
                        
                        # Envoyer le code de vérification par email
                        if two_fa.send_verification_email(request):
                            messages.info(request, 'Un code de vérification a été envoyé à votre adresse email.')
                            return redirect('two_factor_verify')
                        else:
                            messages.error(request, "Une erreur est survenue lors de l'envoi du code de vérification.")
                            return render(request, 'registration/login.html', {'form': form})
                            
                    except Exception as e:
                        logger.error(f"Erreur lors de la connexion 2FA pour {user.username}: {str(e)}")
                        messages.error(request, "Une erreur est survenue lors de l'authentification.")
                        return render(request, 'registration/login.html', {'form': form})
                else:
                    # Si la 2FA est désactivée (ne devrait pas arriver avec la configuration par défaut)
                    auth_login(request, user)
                    return redirect(settings.LOGIN_REDIRECT_URL)
        
        # Si le formulaire n'est pas valide, réafficher le formulaire avec les erreurs
        return render(request, 'registration/login.html', {'form': form})
    
    # Si la méthode est GET, afficher le formulaire de connexion
    form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})
