# Generated by Django 2.2 on 2020-02-21 23:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('spotify', '0002_auto_20200219_1558'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='playlistgroup',
            constraint=models.UniqueConstraint(fields=('name',), name='unique_constraint_group_name'),
        ),
    ]
