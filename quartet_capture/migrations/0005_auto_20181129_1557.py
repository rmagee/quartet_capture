# Generated by Django 2.1.3 on 2018-11-29 21:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quartet_capture', '0004_auto_20181129_1504'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filter',
            name='name',
            field=models.CharField(help_text='The name of the filter.', max_length=100, unique=True, verbose_name='Name'),
        ),
    ]
