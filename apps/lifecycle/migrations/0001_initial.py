"""Initial migration for the lifecycle app.

Adopts CallbackLog state from portfolio (table already exists in the DB
on installs that ran portfolio.0069). Also creates the brand-new
LifecycleEvent table.
"""

from __future__ import annotations

import django_extensions.db.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    """Adopt CallbackLog state and create LifecycleEvent table."""

    initial = True

    dependencies = [
        ('portfolio', '0072_move_callback_log_to_lifecycle'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name='CallbackLog',
                    fields=[
                        (
                            'id',
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name='ID',
                            ),
                        ),
                        (
                            'created',
                            django_extensions.db.fields
                            .CreationDateTimeField(
                                auto_now_add=True,
                                verbose_name='created',
                            ),
                        ),
                        (
                            'modified',
                            django_extensions.db.fields
                            .ModificationDateTimeField(
                                auto_now=True,
                                verbose_name='modified',
                            ),
                        ),
                        (
                            'stage_type',
                            models.CharField(
                                choices=[
                                    ('portfolio', 'portfolio'),
                                    ('rebalance_event', 'rebalance_event'),
                                    ('phase', 'phase'),
                                    ('order', 'order'),
                                    ('basket', 'basket'),
                                ],
                                max_length=32,
                            ),
                        ),
                        ('stage_id', models.BigIntegerField()),
                        (
                            'callback_ref',
                            models.CharField(max_length=128, unique=True),
                        ),
                        (
                            'direction',
                            models.CharField(
                                choices=[
                                    ('inbound', 'inbound'),
                                    ('outbound', 'outbound'),
                                ],
                                max_length=16,
                            ),
                        ),
                        (
                            'target_service',
                            models.CharField(max_length=64),
                        ),
                        (
                            'status',
                            models.CharField(
                                choices=[
                                    ('processing', 'processing'),
                                    ('completed', 'completed'),
                                    ('failed', 'failed'),
                                ],
                                default='processing',
                                max_length=16,
                            ),
                        ),
                        (
                            'idempotency_key',
                            models.CharField(max_length=256, unique=True),
                        ),
                        ('request_payload', models.JSONField(default=dict)),
                        ('response_payload', models.JSONField(default=dict)),
                        (
                            'reason',
                            models.TextField(blank=True, null=True),
                        ),
                    ],
                    options={
                        'db_table': 'callback_log',
                    },
                ),
                migrations.AddIndex(
                    model_name='callbacklog',
                    index=models.Index(
                        fields=['stage_type', 'stage_id'],
                        name='cblog_stage_idx',
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='LifecycleEvent',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'stage_type',
                    models.CharField(
                        choices=[
                            ('portfolio', 'portfolio'),
                            ('rebalance_event', 'rebalance_event'),
                            ('phase', 'phase'),
                            ('order', 'order'),
                            ('basket', 'basket'),
                        ],
                        max_length=32,
                    ),
                ),
                ('stage_id', models.BigIntegerField()),
                (
                    'event_type',
                    models.CharField(
                        choices=[
                            ('created', 'created'),
                            ('state_changed', 'state_changed'),
                            ('transition_applied', 'transition_applied'),
                            ('guard_failed', 'guard_failed'),
                            ('leg_updated', 'leg_updated'),
                            ('error', 'error'),
                        ],
                        max_length=32,
                    ),
                ),
                (
                    'from_state',
                    models.CharField(
                        blank=True,
                        max_length=50,
                        null=True,
                    ),
                ),
                (
                    'to_state',
                    models.CharField(
                        blank=True,
                        max_length=50,
                        null=True,
                    ),
                ),
                ('actor', models.CharField(max_length=128)),
                (
                    'trigger',
                    models.CharField(
                        choices=[
                            ('api', 'api'),
                            ('callback', 'callback'),
                            ('scheduled', 'scheduled'),
                            ('manual', 'manual'),
                            ('system', 'system'),
                        ],
                        max_length=32,
                    ),
                ),
                (
                    'guard_code',
                    models.CharField(
                        blank=True,
                        max_length=64,
                        null=True,
                    ),
                ),
                (
                    'idempotency_key',
                    models.CharField(
                        blank=True,
                        db_index=True,
                        max_length=256,
                        null=True,
                    ),
                ),
                (
                    'correlation_id',
                    models.CharField(
                        blank=True,
                        db_index=True,
                        max_length=128,
                        null=True,
                    ),
                ),
                ('payload', models.JSONField(default=dict)),
                ('occurred_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'lifecycle_event',
                'ordering': ['occurred_at', 'id'],
            },
        ),
        migrations.AddIndex(
            model_name='lifecycleevent',
            index=models.Index(
                fields=['stage_type', 'stage_id', 'occurred_at'],
                name='lcevt_stage_occ_idx',
            ),
        ),
    ]
