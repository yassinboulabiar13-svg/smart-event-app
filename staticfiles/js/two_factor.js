// Gestion du renvoi du code 2FA
document.addEventListener('DOMContentLoaded', function() {
    const resendButton = document.getElementById('resend-code');
    
    if (resendButton) {
        resendButton.addEventListener('click', function() {
            const url = this.getAttribute('data-url');
            const csrfToken = this.getAttribute('data-csrf');
            const buttonText = this.innerHTML;
            
            // Désactiver le bouton pendant 60 secondes
            this.disabled = true;
            let seconds = 60;
            
            const countdown = setInterval(() => {
                this.innerHTML = `Renvoyer (${seconds}s)`;
                seconds--;
                
                if (seconds < 0) {
                    clearInterval(countdown);
                    this.innerHTML = buttonText;
                    this.disabled = false;
                }
            }, 1000);
            
            // Envoyer la requête AJAX pour renvoyer le code
            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('Un nouveau code a été envoyé à votre adresse email.', 'success');
                } else {
                    showAlert('Erreur lors de l\'envoi du code. Veuillez réessayer.', 'danger');
                    clearInterval(countdown);
                    this.innerHTML = buttonText;
                    this.disabled = false;
                }
            })
            .catch(error => {
                console.error('Erreur:', error);
                showAlert('Une erreur est survenue. Veuillez réessayer.', 'danger');
                clearInterval(countdown);
                this.innerHTML = buttonText;
                this.disabled = false;
            });
        });
    }
    
    // Fonction pour afficher une alerte
    function showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show mt-3`;
        alertDiv.role = 'alert';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        const container = document.querySelector('.card-body');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
            
            // Supprimer l'alerte après 5 secondes
            setTimeout(() => {
                alertDiv.remove();
            }, 5000);
        }
    }
    
    // Validation du formulaire de code 2FA
    const form = document.querySelector('form.needs-validation');
    if (form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    }
});
