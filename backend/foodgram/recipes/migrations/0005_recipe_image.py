# Generated by Django 3.2 on 2023-08-05 19:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0004_auto_20230805_2205'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='image',
            field=models.ImageField(default='no_photo.jpg', upload_to='images/'),
        ),
    ]
