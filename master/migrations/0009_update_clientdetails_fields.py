# Generated migration to update ClientDetails fields to new schema
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('master', '0008_rename_party_to_clientdetails'),
    ]

    operations = [
        # Rename existing fields to new names where appropriate
        migrations.RenameField(
            model_name='clientdetails',
            old_name='add1',
            new_name='address',
        ),
        migrations.RenameField(
            model_name='clientdetails',
            old_name='city',
            new_name='area',
        ),
        migrations.RenameField(
            model_name='clientdetails',
            old_name='gst',
            new_name='client_type',
        ),
        # Remove unused fields
        migrations.RemoveField(
            model_name='clientdetails',
            name='add2',
        ),
        migrations.RemoveField(
            model_name='clientdetails',
            name='email',
        ),
        migrations.RemoveField(
            model_name='clientdetails',
            name='remarks',
        ),
        # Add new fields
        migrations.AddField(
            model_name='clientdetails',
            name='phone',
            field=models.CharField(max_length=15, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='clientdetails',
            name='crlimit',
            field=models.DecimalField(max_digits=12, decimal_places=2, default=0.0),
        ),
        migrations.AddField(
            model_name='clientdetails',
            name='crdays',
            field=models.IntegerField(default=0),
        ),
        # Alter field verbose names and db_columns are handled in models.py; no DB rename needed where db_column kept
    ]
