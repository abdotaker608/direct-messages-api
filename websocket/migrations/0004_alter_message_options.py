# Generated by Django 3.2.2 on 2021-05-28 13:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('websocket', '0003_alter_chat_users'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='message',
            options={'ordering': ('-created',)},
        ),
    ]
