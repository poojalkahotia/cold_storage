from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('master', '0012_rename_gpmaster_client_name_to_client_details'),
    ]

    operations = [
        migrations.RenameField(
            model_name='payment',
            old_name='party',
            new_name='client_details',
        ),
    ]
