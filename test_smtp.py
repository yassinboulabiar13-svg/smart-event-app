import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration
smtp_server = "smtp.gmail.com"
port = 587  # Pour le démarrage TLS
sender_email = "yassinboulabiar13@gmail.com"
password = input("Entrez votre mot de passe d'application: ")
receiver_email = "yassinboulabiar13@gmail.com"

# Création du message
message = MIMEMultipart("alternative")
message["Subject"] = "Test SMTP Python"
message["From"] = sender_email
message["To"] = receiver_email

# Création du contenu du message
text = """\
Bonjour,

Ceci est un test d'envoi d'email via SMTP Python.

Cordialement,
Smart Event"""

# Ajout du contenu au message
part1 = MIMEText(text, "plain")
message.attach(part1)

# Connexion et envoi du message
try:
    print("Connexion au serveur SMTP...")
    with smtplib.SMTP(smtp_server, port) as server:
        server.ehlo()
        print("Démarrage de la session TLS...")
        server.starttls()
        server.ehlo()
        
        print("Authentification...")
        server.login(sender_email, password)
        
        print("Envoi de l'email...")
        server.sendmail(sender_email, receiver_email, message.as_string())
        
    print("Email envoyé avec succès!")
    
except Exception as e:
    print(f"Erreur: {e}")
