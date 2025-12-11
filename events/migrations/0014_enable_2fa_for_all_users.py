from django.db import migrations

def enable_2fa_for_all_users(apps, schema_editor):
    """Active la 2FA pour tous les utilisateurs existants"""
    User = apps.get_model('auth', 'User')
    TwoFactorAuth = apps.get_model('events', 'TwoFactorAuth')
    
    # Activer la 2FA pour tous les utilisateurs
    for user in User.objects.all():
        TwoFactorAuth.objects.get_or_create(
            user=user,
            defaults={'is_enabled': True}
        )

class Migration(migrations.Migration):

    dependencies = [
        ('events', '0013_twofactorauth_twofactorcode'),  # Dernière migration existante
    ]

    operations = [
        migrations.RunPython(enable_2fa_for_all_users, migrations.RunPython.noop),
    ]
