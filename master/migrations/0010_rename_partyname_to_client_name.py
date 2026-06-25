from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('master', '0009_update_clientdetails_fields'),
    ]

    operations = [
        migrations.RenameField(
            model_name='clientdetails',
            old_name='partyname',
            new_name='client_name',
        ),
    ]
