# Generated by Django 2.2.9 on 2020-06-10 05:40

from django.db import migrations, models
import django.db.models.deletion
import wagtail.core.models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0045_assign_unlock_grouppagepermission'),
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='collection',
            field=models.ForeignKey(default=wagtail.core.models.get_root_collection_id, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='wagtailcore.Collection', verbose_name='collection'),
        ),
    ]
