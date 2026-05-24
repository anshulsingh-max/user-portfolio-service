"""Phase 0 / B7 — add CallbackLog table (prep for Phase 1).

Additive only; nothing reads or writes this table yet. The Phase 1
TransitionService will use it as the authoritative idempotency record
for broker / async callbacks.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0068_phase0_basket_end_amount_decimal'),
    ]

    operations = [
        migrations.CreateModel(
            name='CallbackLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='modified')),
                ('stage_type', models.CharField(choices=[
                    ('portfolio', 'portfolio'),
                    ('rebalance_event', 'rebalance_event'),
                    ('phase', 'phase'),
                    ('order', 'order'),
                    ('basket', 'basket'),
                ], max_length=32)),
                ('stage_id', models.BigIntegerField()),
                ('callback_ref', models.CharField(max_length=128, unique=True)),
                ('direction', models.CharField(choices=[
                    ('inbound', 'inbound'),
                    ('outbound', 'outbound'),
                ], max_length=16)),
                ('target_service', models.CharField(max_length=64)),
                ('status', models.CharField(choices=[
                    ('processing', 'processing'),
                    ('completed', 'completed'),
                    ('failed', 'failed'),
                ], default='processing', max_length=16)),
                ('idempotency_key', models.CharField(max_length=256, unique=True)),
                ('request_payload', models.JSONField(default=dict)),
                ('response_payload', models.JSONField(default=dict)),
                ('reason', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'callback_log',
            },
        ),
        migrations.AddIndex(
            model_name='callbacklog',
            index=models.Index(fields=['stage_type', 'stage_id'], name='cblog_stage_idx'),
        ),
    ]
