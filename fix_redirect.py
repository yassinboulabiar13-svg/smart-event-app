# Script pour corriger la redirection après création d'un événement privé
def fix_redirect():
    file_path = r"c:\Users\ovic\smart_event - Copie\events\views.py"
    
    # Lire le contenu actuel du fichier
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Remplacer la ligne de redirection pour aller vers le dashboard
    new_content = content.replace(
        "            return redirect('event_detail', event_type='public', event_id=event.id)",
        "            return redirect('dashboard')  # Redirection vers le tableau de bord après création"
    )
    
    # Écrire le nouveau contenu dans le fichier
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(new_content)
    
    print("La correction de redirection a été appliquée avec succès. Vous serez maintenant redirigé vers le tableau de bord après la création d'un événement privé.")

if __name__ == "__main__":
    fix_redirect()
