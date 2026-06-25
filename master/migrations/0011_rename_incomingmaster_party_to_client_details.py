from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('master', '0010_rename_partyname_to_client_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='incomingmaster',
            old_name='party',
            new_name='client_details',
        ),
    ]
