# Generated by Django 5.1.6 on 2025-02-13 02:16

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AreaInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('barangay', models.TextField(blank=True, null=True)),
                ('city', models.TextField(blank=True, null=True)),
                ('province', models.TextField(blank=True, null=True)),
                ('commune_id', models.TextField(blank=True, null=True)),
                ('district_id', models.TextField(blank=True, null=True)),
                ('province_id', models.TextField(blank=True, null=True)),
                ('ai_province', models.TextField(blank=True, null=True)),
                ('ai_city', models.TextField(blank=True, null=True)),
                ('ai_barangay', models.TextField(blank=True, null=True)),
            ],
            options={
                'indexes': [models.Index(fields=['barangay'], name='barangay_idx'), models.Index(fields=['city'], name='city_idx'), models.Index(fields=['province'], name='province_idx'), models.Index(fields=['commune_id'], name='commune_id_idx'), models.Index(fields=['district_id'], name='district_id_idx'), models.Index(fields=['province_id'], name='province_id_idx')],
            },
        ),
    ]
