"""Lifecycle side-effect services extracted from apps/portfolio/signals.py.

Each function mirrors the body of one post_save receiver verbatim.
Nothing calls these yet; they are the named contract that subsequent
passes (section 7.8 step 3 repoint, step 4 thin-adapter) will route to.
"""

from __future__ import annotations

from apps.lifecycle.services.basket_effects import apply_basket_effects
from apps.lifecycle.services.order_effects import apply_order_effects
from apps.lifecycle.services.order_instruction_effects import (
    apply_order_instruction_effects,
)
from apps.lifecycle.services.rebalance_transaction_effects import (
    apply_rebalance_transaction_effects,
)
from apps.lifecycle.services.user_instruction_effects import (
    apply_user_instruction_effects,
)
from apps.lifecycle.services.user_portfolio_effects import (
    apply_user_portfolio_effects,
)
from apps.lifecycle.services.user_portfolio_rebalance_effects import (
    apply_user_portfolio_rebalance_effects,
)

__all__ = [
    "apply_basket_effects",
    "apply_order_effects",
    "apply_order_instruction_effects",
    "apply_rebalance_transaction_effects",
    "apply_user_instruction_effects",
    "apply_user_portfolio_effects",
    "apply_user_portfolio_rebalance_effects",
]
