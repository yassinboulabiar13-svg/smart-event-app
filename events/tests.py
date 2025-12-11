from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from django.template.loader import get_template
from django.template import TemplateDoesNotExist

class TemplateCheckTest(TestCase):
    def test_add_private_event_template_exists(self):
        """Vérifie que le template add_private_event.html existe"""
        try:
            template = get_template('events/add_private_event.html')
            print("✅ Template trouvé !")
        except TemplateDoesNotExist as e:
            print("❌ Template non trouvé !")
            print("Django a cherché dans :")
            for origin in e.tried:
                print("-", origin)
            raise e  # relance l'erreur pour que le test échoue
