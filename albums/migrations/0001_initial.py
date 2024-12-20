# Generated by Django 5.1.3 on 2024-12-09 09:30

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('artists', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Album',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('cover', models.ImageField(blank=True, null=True, upload_to='albums')),
                ('genre', models.CharField(blank=True, max_length=50, null=True)),
                ('year', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(limit_value=0)])),
                ('artist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='artists.artist')),
            ],
            options={
                'constraints': [models.UniqueConstraint(fields=('artist_id', 'name'), name='unique_artist_album')],
            },
        ),
    ]
