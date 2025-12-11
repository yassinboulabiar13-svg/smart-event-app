import os

# Chemin du fichier settings.py
settings_path = os.path.join(os.path.dirname(__file__), 'smart_event', 'settings.py')

# Lire le contenu actuel
with open(settings_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Remplacer la configuration email
new_config = """# === Email Configuration ===
# Chargement des variables d'environnement
load_dotenv()

# Configuration Gmail avec SSL
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'yassinboulabiar13@gmail.com'
EMAIL_HOST_PASSWORD = 'fqyyntngsszpkri'  # Utilisation du mot de passe d'application
DEFAULT_FROM_EMAIL = 'Smart Event <yassinboulabiar13@gmail.com>'
SERVER_EMAIL = 'yassinboulabiar13@gmail.com'
"""

# Remplacer la section email existante
start_marker = '# === Email Configuration ==='
end_marker = '# Configuration pour éviter les erreurs de connexion'

if start_marker in content and end_marker in content:
    before = content.split(start_marker)[0]
    after = content.split(end_marker)[1]
    new_content = before + new_config + end_marker + after
    
    # Écrire les modifications
    with open(settings_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

print("Configuration des emails mise à jour avec succès !")
print("\nNouvelle configuration :")
print("-" * 50)
print("EMAIL_HOST = smtp.gmail.com")
print("EMAIL_PORT = 465")
print("EMAIL_USE_SSL = True")
print("EMAIL_HOST_USER = yassinboulabiar13@gmail.com")
print("EMAIL_HOST_PASSWORD = fqyyntngsszpkri")
print("DEFAULT_FROM_EMAIL = Smart Event <yassinboulabiar13@gmail.com>")
print("-" * 50)
print("\nPour appliquer les modifications :")
print("1. Redémarrez votre serveur Django")
print("2. Testez avec: python test_email_smtp.py")
