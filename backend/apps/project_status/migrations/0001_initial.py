# Generated initial migration for project_status

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectPhase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(db_index=True, default=0)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('completed', 'Completada'), ('in_progress', 'En progreso'), ('pending', 'Pendiente'), ('blocked', 'Bloqueada')], default='pending', max_length=20)),
                ('date_completed', models.DateField(blank=True, null=True)),
                ('github_url', models.URLField(blank=True)),
                ('doc_url', models.URLField(blank=True)),
            ],
            options={
                'ordering': ['order'],
                'verbose_name': 'fase del proyecto',
                'verbose_name_plural': 'fases del proyecto',
            },
        ),
        migrations.CreateModel(
            name='ProjectModule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(db_index=True, default=0)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('live', 'En producción'), ('beta', 'Beta'), ('alpha', 'Alpha'), ('pending', 'Pendiente')], default='pending', max_length=20)),
                ('icon', models.CharField(blank=True, help_text='Emoji o icono corto', max_length=20)),
            ],
            options={
                'ordering': ['order'],
                'verbose_name': 'módulo',
                'verbose_name_plural': 'módulos',
            },
        ),
    ]
