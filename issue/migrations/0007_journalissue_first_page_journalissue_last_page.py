from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('issue', '0006_alter_journalissue_doi'),
    ]

    operations = [
        migrations.AddField(
            model_name='journalissue',
            name='first_page',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
        migrations.AddField(
            model_name='journalissue',
            name='last_page',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
    ]
