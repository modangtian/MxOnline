# Generated by Django 2.0.2 on 2018-04-26 13:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0007_auto_20180424_2047'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseorg',
            name='tag',
            field=models.CharField(default='全国知名', max_length=10, verbose_name='机构标签'),
        ),
    ]
