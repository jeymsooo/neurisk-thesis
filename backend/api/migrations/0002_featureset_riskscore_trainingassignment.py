# Generated by Django 5.2.2 on 2025-06-08 17:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeatureSet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('features', models.JSONField(help_text='Extracted features from EMG data')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('emg_data', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feature_sets', to='api.emgdata')),
            ],
        ),
        migrations.CreateModel(
            name='RiskScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.FloatField(help_text='Predicted risk score (numeric)')),
                ('level', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], max_length=20)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('feature_set', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='risk_scores', to='api.featureset')),
            ],
        ),
        migrations.CreateModel(
            name='TrainingAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assignment', models.TextField(help_text='Assigned training based on risk score')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('risk_score', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='training_assignments', to='api.riskscore')),
            ],
        ),
    ]
