from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crossref', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='depositbatch',
            name='kind',
            field=models.CharField(
                choices=[('new', 'Register new DOIs'),
                         ('update', 'Update metadata of existing DOIs')],
                default='new',
                help_text=(
                    'A new batch mints DOIs for articles that have none. An update re-sends '
                    'existing DOIs with corrected metadata, and must never clear a DOI from its '
                    'article when it fails — the DOI is already registered and permanent.'
                ),
                max_length=20,
            ),
        ),
    ]
