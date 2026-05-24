"""Phase 0 / C3 — re-add `unique_user_subscription` on UserPortfolio.

The constraint was commented out in migration 0059 because duplicates
existed. Plan §6 / §13.3 calls for dedup + reinstating it.

Dedup policy: per (user_id, subscription_id, portfolio_id, status) keep
the most-recent row by `created` desc, then `id` desc; delete the rest.
History rows in `simple_history` are kept (the historicalrecords table
is not touched).

Counts deleted vs kept are logged. The migration is irreversible — the
reverse op just removes the constraint and does NOT resurrect deleted
rows.
"""

import logging
from collections import defaultdict

from django.db import migrations, models


logger = logging.getLogger("portfolio.migrations.0070")


def dedupe_user_portfolio(apps, schema_editor):
    UserPortfolio = apps.get_model("portfolio", "UserPortfolio")

    groups = defaultdict(list)
    for row in UserPortfolio.objects.all().only(
        "id", "user_id", "subscription_id", "portfolio_id", "status", "created"
    ):
        key = (row.user_id, row.subscription_id, row.portfolio_id, row.status)
        groups[key].append(row)

    kept = 0
    deleted = 0
    for key, rows in groups.items():
        if len(rows) <= 1:
            kept += 1
            continue
        rows.sort(key=lambda r: (r.created, r.id), reverse=True)
        keeper = rows[0]
        losers = rows[1:]
        loser_ids = [r.id for r in losers]
        logger.warning(
            "UserPortfolio dedup key=%r keeping id=%s deleting ids=%s",
            key, keeper.id, loser_ids,
        )
        UserPortfolio.objects.filter(id__in=loser_ids).delete()
        kept += 1
        deleted += len(losers)

    logger.info(
        "UserPortfolio dedup complete: groups=%d kept=%d deleted=%d",
        len(groups), kept, deleted,
    )


def noop_reverse(apps, schema_editor):
    # Cannot undelete dropped duplicate rows. Constraint removal is handled
    # by RemoveConstraint's automatic reverse.
    return


class Migration(migrations.Migration):
    # Postgres refuses ALTER TABLE ... ADD CONSTRAINT while FK / history-table
    # trigger events from the dedup DELETEs are still deferred inside the same
    # transaction ("cannot ALTER TABLE ... because it has pending trigger
    # events"). Running the migration non-atomically lets the RunPython commit
    # so triggers drain before AddConstraint executes.
    atomic = False

    dependencies = [
        ("portfolio", "0069_phase0_callback_log"),
    ]

    operations = [
        migrations.RunPython(dedupe_user_portfolio, noop_reverse),
        migrations.AddConstraint(
            model_name="userportfolio",
            constraint=models.UniqueConstraint(
                fields=["user_id", "subscription_id", "portfolio_id", "status"],
                name="unique_user_subscription",
            ),
        ),
    ]
