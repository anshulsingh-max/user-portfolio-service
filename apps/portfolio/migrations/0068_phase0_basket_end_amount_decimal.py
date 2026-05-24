"""Phase 0 / C2 — Basket.end_amount: CharField -> DecimalField.

Money values must not live in text columns. This migration:

1. Adds a new DecimalField `end_amount_dec` alongside the old `end_amount`.
2. Copies each row's CharField value into the new column, coercing through
   Decimal. Non-numeric / blank values are stored as NULL and counted in
   the migration log.
3. Drops the old CharField.
4. Renames `end_amount_dec` -> `end_amount`.

Reverse migration is best-effort: we cast Decimal back to its string form;
historical NULLs become empty strings.
"""

from decimal import Decimal, InvalidOperation
import logging

from django.db import migrations, models


logger = logging.getLogger("portfolio.migrations.0068")


def _coerce_to_decimal(raw):
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return None


def copy_char_to_decimal(apps, schema_editor):
    Basket = apps.get_model("portfolio", "Basket")
    total = 0
    migrated = 0
    nulled = 0
    for basket in Basket.objects.all().iterator(chunk_size=500):
        total += 1
        value = _coerce_to_decimal(basket.end_amount)
        basket.end_amount_dec = value
        if value is None:
            nulled += 1
            if basket.end_amount not in (None, "", "0.0", "0"):
                logger.warning(
                    "Basket %s end_amount=%r could not be parsed as Decimal; set NULL",
                    basket.pk, basket.end_amount,
                )
        else:
            migrated += 1
        basket.save(update_fields=["end_amount_dec"])
    logger.info(
        "Basket.end_amount Char->Decimal migration: total=%d migrated=%d nulled=%d",
        total, migrated, nulled,
    )


def copy_decimal_to_char(apps, schema_editor):
    Basket = apps.get_model("portfolio", "Basket")
    for basket in Basket.objects.all().iterator(chunk_size=500):
        basket.end_amount = "" if basket.end_amount_dec is None else str(basket.end_amount_dec)
        basket.save(update_fields=["end_amount"])


class Migration(migrations.Migration):

    dependencies = [
        ("portfolio", "0067_phase0_callable_defaults"),
    ]

    operations = [
        migrations.AddField(
            model_name="basket",
            name="end_amount_dec",
            field=models.DecimalField(
                max_digits=20, decimal_places=4, null=True, blank=True
            ),
        ),
        migrations.RunPython(copy_char_to_decimal, copy_decimal_to_char),
        migrations.RemoveField(
            model_name="basket",
            name="end_amount",
        ),
        migrations.RenameField(
            model_name="basket",
            old_name="end_amount_dec",
            new_name="end_amount",
        ),
    ]
