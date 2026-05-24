"""Move CallbackLog state ownership from portfolio to lifecycle app.

Uses SeparateDatabaseAndState so the existing callback_log table is left
intact. The lifecycle app's 0001_initial adopts the model into its own
state in a paired state_operations CreateModel.
"""

from __future__ import annotations

from django.db import migrations


class Migration(migrations.Migration):
    """State-only delete; the database table stays for lifecycle to adopt."""

    dependencies = [
        (
            'portfolio',
            '0071_alter_callbacklog_created_alter_callbacklog_id_and_more',
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(name='CallbackLog'),
            ],
        ),
    ]
