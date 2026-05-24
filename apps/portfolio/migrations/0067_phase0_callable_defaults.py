"""Phase 0 / C1 — replace mutable default literals with callables.

`default={}` / `default=[]` share one mutable instance across all model
instances created without an explicit value, which is a Django anti-pattern.
Switch to `default=dict` / `default=list` (callables).

Schema-only AlterField — no data is rewritten.
"""

from django.contrib.postgres.fields import ArrayField
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0066_userinstruction_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='states',
            field=ArrayField(models.CharField(max_length=20), default=list),
        ),
        migrations.AlterField(
            model_name='userportfoliorebalance',
            name='user_inputs',
            field=models.JSONField(default=dict, verbose_name='UserInputs'),
        ),
        migrations.AlterField(
            model_name='userportfoliorebalance',
            name='metadata',
            field=models.JSONField(default=dict, verbose_name='MetaData'),
        ),
        migrations.AlterField(
            model_name='portfoliorebalancetransaction',
            name='allocation_quantity',
            field=models.JSONField(default=dict, verbose_name='UserAllocationQuantity'),
        ),
        migrations.AlterField(
            model_name='portfoliorebalancetransaction',
            name='user_rebalance_json',
            field=models.JSONField(default=dict, verbose_name='UserRebalanceJson'),
        ),
    ]
