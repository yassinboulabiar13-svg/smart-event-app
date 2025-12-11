import os

# Configuration des emails
email_config = """# === Email ===
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=465
EMAIL_USE_SSL=True
EMAIL_HOST_USER=yassinboulabiar13@gmail.com
EMAIL_HOST_PASSWORD=bxlhydrgfenisckl
DEFAULT_FROM_EMAIL='Smart Event <yassinboulabiar13@gmail.com>'
GMAIL_APP_PASSWORD=fqyyntngsszpkri
"""

# Mettre à jour settings.py
settings_path = os.path.join(os.path.dirname(__file__), 'smart_event', 'settings.py')

with open(settings_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Supprimer l'ancienne configuration email
start_marker = '# === Email Configuration ==='
end_marker = '# Configuration pour éviter les erreurs de connexion'

if start_marker in content and end_marker in content:
    before = content.split(start_marker)[0]
    after = content.split(end_marker)[1]
    # Écrire une configuration par défaut sans exposer d'espaces dans le mot de passe
    clean_pass = 'bxlhydrgfenisckl'
    new_content = before + """# === Email Configuration ===
# Chargement des variables d'environnement
load_dotenv()

# Configuration Gmail avec SSL
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'yassinboulabiar13@gmail.com'
EMAIL_HOST_PASSWORD = '""" + clean_pass + """  # Mot de passe sans espaces
DEFAULT_FROM_EMAIL = 'Smart Event <yassinboulabiar13@gmail.com>'
SERVER_EMAIL = 'yassinboulabiar13@gmail.com'
""" + end_marker + after

    with open(settings_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

print("Configuration des emails mise à jour avec succès !")
print("\nNouvelle configuration :")
print("-" * 50)
print("EMAIL_HOST = smtp.gmail.com")
print("EMAIL_PORT = 465")
print("EMAIL_USE_SSL = True")
print("EMAIL_HOST_USER = yassinboulabiar13@gmail.com")
print("DEFAULT_FROM_EMAIL = Smart Event <yassinboulabiar13@gmail.com>")
print("-" * 50)
print("\nRedémarrez votre serveur Django pour appliquer les modifications.")
