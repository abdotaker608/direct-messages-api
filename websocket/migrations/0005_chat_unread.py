# Generated by Django 3.2.2 on 2021-05-28 15:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('websocket', '0004_alter_message_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='unread',
            field=models.IntegerField(default=0),
        ),
    ]
