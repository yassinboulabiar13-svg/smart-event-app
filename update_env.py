import os

# Nouveau mot de passe d'application Gmail
NEW_PASSWORD = "fqyyntngsszpkri"

# Chemin du fichier .env
env_path = os.path.join(os.path.dirname(__file__), '.env')

# Vérifier si le fichier .env existe
if os.path.exists(env_path):
    # Lire le contenu actuel
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Mettre à jour ou ajouter la ligne GMAIL_APP_PASSWORD
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('GMAIL_APP_PASSWORD'):
            lines[i] = f'GMAIL_APP_PASSWORD={NEW_PASSWORD}\n'
            updated = True
    
    if not updated:
        lines.append(f'GMAIL_APP_PASSWORD={NEW_PASSWORD}\n')
    
    # Écrire les modifications
    with open(env_path, 'w') as f:
        f.writelines(lines)
    
    print("Fichier .env mis à jour avec succès !")
else:
    # Créer un nouveau fichier .env
    with open(env_path, 'w') as f:
        f.write(f'GMAIL_APP_PASSWORD={NEW_PASSWORD}\n')
    print("Nouveau fichier .env créé avec succès !")

# Afficher un message de confirmation
print("\nConfiguration mise à jour avec les paramètres suivants :")
print(f"EMAIL_HOST_USER = yassinboulabiar13@gmail.com")
print(f"GMAIL_APP_PASSWORD = {NEW_PASSWORD}\n")

print("Redémarrez votre serveur Django pour appliquer les modifications.")
