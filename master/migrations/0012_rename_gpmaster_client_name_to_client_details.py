from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('master', '0011_rename_incomingmaster_party_to_client_details'),
    ]

    operations = [
        migrations.RenameField(
            model_name='gpmaster',
            old_name='client_name',
            new_name='client_details',
        ),
    ]
