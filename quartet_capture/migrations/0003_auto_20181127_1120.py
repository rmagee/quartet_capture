# Generated by Django 2.1.2 on 2018-11-27 17:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('quartet_capture', '0002_auto_20181001_1407'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='taskhistory',
            options={'ordering': ['created']},
        ),
    ]
