"""
Django settings for smart_event project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# ✅ Correctif SSL (Windows + Python 3.13 + Gmail STARTTLS)
import ssl
import certifi

ssl_context = ssl.create_default_context(cafile=certifi.where())
ssl._create_default_https_context = lambda *args, **kwargs: ssl_context

# === Chargement du .env ===
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# === Sécurité ===
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "insecure-default-key")
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"
ALLOWED_HOSTS = ['*']  # Pour le déploiement, à restreindre en production

# === Applications ===
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # App locale
    'events.apps.EventsConfig',  # Utilisation de la configuration d'application personnalisée

    # Extensions
    'widget_tweaks',
]

# === Middleware ===
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'events.auth_views.TwoFactorMiddleware',  # Middleware pour la vérification 2FA
]

# === URLs principales ===
ROOT_URLCONF = 'smart_event.urls'

# === Templates ===
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            str(BASE_DIR / 'events' / 'templates'),  # Chemin vers les templates de l'application
            str(BASE_DIR / 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'smart_event.wsgi.application'

# === Base de données ===
DATABASES = {
    'default': {
        'ENGINE': os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
        'NAME': os.getenv("DB_NAME", BASE_DIR / "db.sqlite3"),
    }
}

# === Authentification ===
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# === Langue et fuseau horaire ===
LANGUAGE_CODE = 'fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

# === Fichiers statiques ===
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# === Fichiers médias ===
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# === Authentification ===
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# === Session fix ===
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Ou 'django.contrib.sessions.backends.signed_cookies'
SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds
SESSION_SAVE_EVERY_REQUEST = True

# Clear existing problematic sessions
import os
if os.path.exists('session_data'):
    import shutil
    shutil.rmtree('session_data')

# === Email Configuration ===
# Chargement des variables d'environnement (déjà fait plus haut)

# Lecture sécurisée des paramètres d'email depuis l'environnement.
# Pour les mots de passe d'application Gmail, l'UI Google affiche
# souvent la clé en 4 groupes séparés par des espaces — on les
# supprime automatiquement pour éviter une mauvaise saisie.
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '465'))

# Si vous utilisez le port 465, utilisez SSL. Pour 587, utilisez TLS.
if EMAIL_PORT == 465:
    EMAIL_USE_SSL = True
    EMAIL_USE_TLS = False
elif EMAIL_PORT == 587:
    EMAIL_USE_SSL = False
    EMAIL_USE_TLS = True
else:
    # Valeur par défaut conservatrice
    EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False') == 'True'
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'False') == 'True'

EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'yassinboulabiar13@gmail.com')
# Récupère le mot de passe depuis .env ou fallback, puis supprime les espaces
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'bxlh ydrg feni sckl').replace(' ', '')

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', f'Smart Event <{EMAIL_HOST_USER}>')
SERVER_EMAIL = os.getenv('SERVER_EMAIL', EMAIL_HOST_USER)

# Timeout raisonnable
EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', '30'))

# Affichage en mode développement (n'affiche pas le mot de passe)
if DEBUG:
    print('\n' + '='*70)
    print('MODE DÉVELOPPEMENT : Les emails sont envoyés via SMTP')
    print(f'Destinataire par défaut: {EMAIL_HOST_USER}')
    print(f'Host/Port: {EMAIL_HOST}:{EMAIL_PORT} (SSL={EMAIL_USE_SSL} TLS={EMAIL_USE_TLS})')
    print('='*70 + '\n')

# Advanced email settings
EMAIL_SSL_KEYFILE = None
EMAIL_SSL_CERTFILE = None
EMAIL_SSL_CA_CERTS = None

# SSL Configuration: ne pas désactiver la vérification SSL en production
if DEBUG:
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context

# Logging détaillé (défini avant d'être utilisé)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'logs/debug.log',
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.core.mail': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'events.views': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        # Logger spécifique pour le suivi des emails
        'email_logger': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Désactiver le mode debug pour envoyer de vrais emails
EMAIL_DEBUG = False

# Affichage de la configuration email
print("\n" + "="*50)
print("CONFIGURATION EMAIL")
print("="*50)
print(f"EMAIL_BACKEND: {EMAIL_BACKEND}")
print(f"EMAIL_HOST: {EMAIL_HOST}")
print(f"EMAIL_PORT: {EMAIL_PORT}")
print(f"EMAIL_USE_TLS: {EMAIL_USE_TLS}")
print(f"EMAIL_HOST_USER: {EMAIL_HOST_USER}")
print(f"DEFAULT_FROM_EMAIL: {DEFAULT_FROM_EMAIL}")
print("="*50 + "\n")

# settings.py
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # Important pour la collecte
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Ajoutez WhiteNoise pour la gestion des fichiers statiques
MIDDLEWARE = [
    # ...
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Ajoutez cette ligne
    'django.middleware.security.SecurityMiddleware',
    # ...
]

# Activez la compression pour les fichiers statiques
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'