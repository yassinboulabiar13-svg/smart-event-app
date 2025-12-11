# Fichier temporaire pour appliquer la correction de la redirection
def apply_fix():
    file_path = r"c:\Users\ovic\smart_event - Copie\events\views.py"
    
    # Lire le contenu actuel du fichier
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Remplacer la ligne problématique
    new_content = content.replace(
        "            return redirect('event_detail', event_type='public', event_id=event.id)",
        "            return redirect('event_detail', event_type='private', event_id=event.id)",
        1  # Remplacer uniquement la première occurrence
    )
    
    # Écrire le nouveau contenu dans le fichier
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(new_content)
    
    print("La correction a été appliquée avec succès.")

if __name__ == "__main__":
    apply_fix()
